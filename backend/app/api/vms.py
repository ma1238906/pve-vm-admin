from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.api import deps
from app.models import user as user_model
from app.models import vm as vm_model
from app.schemas import vm as vm_schema
from app.services.pve import pve_service
from app.core.config import settings
import websockets
import ssl
import asyncio
import urllib.parse

router = APIRouter()

# --- Admin Operations ---

@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_stats(
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    """
    Get PVE Cluster Status for Dashboard.
    """
    try:
        nodes = pve_service.get_nodes()
        # Filter online nodes
        online_nodes = [n for n in nodes if n.get('status') == 'online']
        
        # Aggregate resources
        total_cpu = 0
        used_cpu = 0
        total_mem = 0
        used_mem = 0
        
        for node in online_nodes:
            total_cpu += node.get('maxcpu', 0)
            used_cpu += node.get('cpu', 0) * node.get('maxcpu', 0) # cpu is percentage 0-1
            total_mem += node.get('maxmem', 0)
            used_mem += node.get('mem', 0)

        return {
            "nodes_count": len(nodes),
            "online_nodes": len(online_nodes),
            "total_cpu": total_cpu,
            "used_cpu": used_cpu,
            "total_mem": total_mem,
            "used_mem": used_mem,
            "nodes": nodes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")

@router.get("/templates", response_model=List[Any])
def list_templates(
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    """
    Get all VMs that are templates.
    """
    vms = pve_service.get_vms()
    templates = [vm for vm in vms if vm.get('template') == 1]
    return templates

@router.post("/clone", response_model=vm_schema.VM)
def clone_vm(
    *,
    db: Session = Depends(deps.get_db),
    vm_in: vm_schema.VMCreate,
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    """
    Clone a VM and assign to user.
    """
    # 1. Get next VMID
    new_vmid = int(pve_service.get_next_vmid())
    
    # 2. Clone in PVE
    try:
        pve_service.clone_vm(
            node=vm_in.node,
            vmid=vm_in.vmid,
            newid=new_vmid,
            name=vm_in.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PVE Clone failed: {str(e)}")

    # 3. Create Record in DB
    db_vm = vm_model.VM(
        vmid=new_vmid,
        node=vm_in.node,
        name=vm_in.name,
        owner_id=vm_in.owner_id
    )
    db.add(db_vm)
    db.commit()
    db.refresh(db_vm)
    return db_vm

@router.post("/import", response_model=vm_schema.VM)
def import_vm(
    *,
    db: Session = Depends(deps.get_db),
    vm_in: vm_schema.VMImport,
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    """
    Import an existing PVE VM into the database and assign to user.
    """
    # Check if already exists
    existing = db.query(vm_model.VM).filter(vm_model.VM.vmid == vm_in.vmid).first()
    if existing:
         raise HTTPException(status_code=400, detail="VM already managed in system")

    db_vm = vm_model.VM(
        vmid=vm_in.vmid,
        node=vm_in.node,
        name=vm_in.name,
        owner_id=vm_in.owner_id
    )
    db.add(db_vm)
    db.commit()
    db.refresh(db_vm)
    return db_vm

@router.delete("/{vmid}")
def delete_vm_entry(
    vmid: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_superuser),
):
    """
    Delete VM from DB and PVE
    """
    # 1. Find in DB
    vm_db = db.query(vm_model.VM).filter(vm_model.VM.vmid == vmid).first()
    
    # 2. Delete in PVE
    try:
        if vm_db:
             pve_service.delete_vm(vm_db.node, vmid)
        else:
             # If we don't have DB record, we can't easily delete from PVE without knowing the node.
             # In a real scenario, we might want to pass 'node' as query param to allow deleting orphan PVE VMs.
             pass
    except Exception as e:
        # Proceed to delete from DB even if PVE delete fails (maybe already deleted)
        pass

    if vm_db:
        db.delete(vm_db)
        db.commit()
    
    return {"status": "deleted"}


@router.get("/", response_model=List[vm_schema.VMDetail])
def list_vms(
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    """
    List VMs. 
    - Admin: Merges PVE list and DB list.
    - User: Sees only assigned DB VMs.
    """
    
    # 1. Fetch PVE Data (Admin only usually, but let's do it for status sync)
    # Optimization: Only fetch PVE list if admin. Regular users only need status for their VMs.
    
    pve_vms_map = {}
    if current_user.is_superuser:
        try:
            pve_vms_list = pve_service.get_vms()
            pve_vms_map = {int(vm.get('vmid')): vm for vm in pve_vms_list if str(vm.get('vmid')).isdigit()}
        except Exception as e:
            print(f"Error fetching PVE VMs: {e}")

    # 2. Fetch DB Data
    if current_user.is_superuser:
        db_vms = db.query(vm_model.VM).all()
    else:
        db_vms = current_user.vms

    db_vms_map = {vm.vmid: vm for vm in db_vms}
    
    results = []

    # If Admin: Show Union
    if current_user.is_superuser:
        all_vmids = set(pve_vms_map.keys()) | set(db_vms_map.keys())
        
        for vmid in all_vmids:
            in_pve = vmid in pve_vms_map
            in_db = vmid in db_vms_map
            
            vm_detail = None
            
            if in_pve and in_db:
                # Normal: Synced
                pve_info = pve_vms_map[vmid]
                db_info = db_vms_map[vmid]
                template_flag = bool(pve_info.get('template'))
                os_type = None
                try:
                    os_type = pve_service.get_vm_ostype(db_info.node, vmid)
                except Exception:
                    os_type = None
                ip_addr = None
                if pve_info.get('status') == 'running':
                    try:
                        ip_addr = pve_service.get_vm_ip(db_info.node, vmid)
                    except Exception:
                        ip_addr = None
                vm_detail = vm_schema.VMDetail(
                    id=db_info.id,
                    vmid=vmid,
                    node=db_info.node,
                    name=pve_info.get('name') or db_info.name, 
                    owner_id=db_info.owner_id,
                    status=pve_info.get('status', 'unknown'),
                    cpu=pve_info.get('cpu', 0),
                    maxmem=pve_info.get('maxmem', 0),
                    uptime=pve_info.get('uptime', 0),
                    template=template_flag,
                    os_type=os_type,
                    ip=ip_addr,
                    sync_status='ok'
                )
            elif in_pve and not in_db:
                # Orphan: In PVE but not managed
                pve_info = pve_vms_map[vmid]
                # Filter out templates from the main list if desired, but user asked for all VMs.
                # Usually templates are hidden from "Running VMs" list, but let's include them with status.
                template_flag = bool(pve_info.get('template'))
                os_type = None
                try:
                    os_type = pve_service.get_vm_ostype(pve_info.get('node', ''), vmid)
                except Exception:
                    os_type = None
                ip_addr = None
                if pve_info.get('status') == 'running':
                    try:
                        ip_addr = pve_service.get_vm_ip(pve_info.get('node', ''), vmid)
                    except Exception:
                        ip_addr = None
                vm_detail = vm_schema.VMDetail(
                    id=None, # No DB ID
                    vmid=vmid,
                    node=pve_info.get('node', ''),
                    name=pve_info.get('name', ''),
                    owner_id=None,
                    status=pve_info.get('status', 'unknown'),
                    cpu=pve_info.get('cpu', 0),
                    maxmem=pve_info.get('maxmem', 0),
                    uptime=pve_info.get('uptime', 0),
                    template=template_flag,
                    os_type=os_type,
                    ip=ip_addr,
                    sync_status='orphan'
                )
            elif in_db and not in_pve:
                # Missing: In DB but not found in PVE
                db_info = db_vms_map[vmid]
                vm_detail = vm_schema.VMDetail(
                    id=db_info.id,
                    vmid=vmid,
                    node=db_info.node,
                    name=db_info.name,
                    owner_id=db_info.owner_id,
                    status='unknown',
                    cpu=0,
                    maxmem=0,
                    uptime=0,
                    template=False,
                    ip=None,
                    sync_status='missing'
                )
            
            if vm_detail:
                results.append(vm_detail)

    else:
        # Regular User: Just their DB VMs, but enrich with PVE status individually (or bulk if optimized)
        # For simplicity, we iterate and fetch status individually as before, 
        # OR we could reuse the bulk fetch if we assume the list is small.
        # Let's keep original logic for users but safer.
        for vm_db in db_vms:
            try:
                # Skip templates for user portal
                if pve_service.is_vm_template(vm_db.node, vm_db.vmid):
                    continue
                status = pve_service.get_vm_status(vm_db.node, vm_db.vmid)
                os_type = pve_service.get_vm_ostype(vm_db.node, vm_db.vmid)
                vm_detail = vm_schema.VMDetail(
                    id=vm_db.id,
                    vmid=vm_db.vmid,
                    node=vm_db.node,
                    name=vm_db.name,
                    owner_id=vm_db.owner_id,
                    status=status.get('status', 'unknown'),
                    cpu=status.get('cpu', 0),
                    maxmem=status.get('maxmem', 0),
                    uptime=status.get('uptime', 0),
                    template=False,
                    os_type=os_type,
                    ip=None,
                    sync_status='ok'
                )
                results.append(vm_detail)
            except Exception:
                # Missing in PVE
                vm_detail = vm_schema.VMDetail(
                    id=vm_db.id,
                    vmid=vm_db.vmid,
                    node=vm_db.node,
                    name=vm_db.name,
                    owner_id=vm_db.owner_id,
                    status='unknown',
                    cpu=0,
                    maxmem=0,
                    uptime=0,
                    template=False,
                    ip=None,
                    sync_status='missing'
                )
                results.append(vm_detail)

    return results

# --- VM Actions ---

@router.post("/{vmid}/start")
def start_vm(
    vmid: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    # Check permission. 
    # If admin and VM is orphan (no DB record), allow? 
    # The current logic requires DB record. 
    # Let's enforce DB record for actions for now, OR allow admins to act on orphans if we pass node.
    # To keep it simple: Actions require management (DB record).
    
    vm = db.query(vm_model.VM).filter(vm_model.VM.vmid == vmid).first()
    if not vm:
        # If admin, maybe we can find it in PVE?
        # But we need the node.
        # Let's stick to "Must be managed".
        raise HTTPException(status_code=404, detail="VM not found in management system")
        
    if not current_user.is_superuser and vm.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    pve_service.start_vm(vm.node, vm.vmid)
    return {"status": "started"}

@router.post("/{vmid}/stop")
def stop_vm(
    vmid: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    vm = db.query(vm_model.VM).filter(vm_model.VM.vmid == vmid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    if not current_user.is_superuser and vm.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    pve_service.stop_vm(vm.node, vm.vmid)
    return {"status": "stopped"}

@router.post("/{vmid}/shutdown")
def shutdown_vm(
    vmid: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    vm = db.query(vm_model.VM).filter(vm_model.VM.vmid == vmid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    if not current_user.is_superuser and vm.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    pve_service.shutdown_vm(vm.node, vm.vmid)
    return {"status": "shutdown initiated"}

@router.post("/{vmid}/reset")
def reset_vm(
    vmid: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    vm = db.query(vm_model.VM).filter(vm_model.VM.vmid == vmid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    if not current_user.is_superuser and vm.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    pve_service.reset_vm(vm.node, vm.vmid)
    return {"status": "reset initiated"}

# --- VNC ---

@router.get("/{vmid}/vnc-ticket")
def get_vnc_ticket(
    vmid: int,
    db: Session = Depends(deps.get_db),
    current_user: user_model.User = Depends(deps.get_current_active_user),
):
    vm = db.query(vm_model.VM).filter(vm_model.VM.vmid == vmid).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    if not current_user.is_superuser and vm.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    response = pve_service.get_vnc_ticket(vm.node, vm.vmid)
    return response

# WebSocket Proxy for VNC
# Note: This is a standalone endpoint, not dependent on 'router' usually if using class based views, 
# but in FastAPI we can just define it. However, WebSockets in routers can be tricky with path params.
# I'll define it here but it might need to be mounted in main.py if prefixes are an issue.
# The path will be /api/v1/vms/ws/vncproxy/{node}/{vmid}
# But wait, the client connects to this. 
# The ticket should be passed in query params.

# SSL Context for PVE connection
pve_ssl_context = ssl.create_default_context()
if not settings.PVE_VERIFY_SSL:
    pve_ssl_context.check_hostname = False
    pve_ssl_context.verify_mode = ssl.CERT_NONE

@router.websocket("/ws/vncproxy/{node}/{vmid}")
async def vnc_proxy(
    websocket: WebSocket, 
    node: str, 
    vmid: int, 
    ticket: str, 
    port: str
):
    # NOTE: WebSocket does not support 'Depends' for Auth easily in the handshake for all clients (browser limitation).
    # Usually the ticket acts as auth. Here the 'ticket' param is the PVE ticket.
    # We should ideally validate a JWT token here too, but standard noVNC client only supports one token param usually.
    # For now, we rely on the fact that the user got the valid PVE ticket from our API (which required Auth).
    
    clean_ticket = urllib.parse.quote(ticket, safe='')
    
    headers = {
        "Authorization": f"PVEAPIToken={settings.PVE_USER}!{settings.PVE_TOKEN_NAME}={settings.PVE_TOKEN_VALUE}",
        "Origin": f"https://{settings.PVE_HOST}:{settings.PVE_PORT}",
    }

    pve_ws_url = (
        f"wss://{settings.PVE_HOST}:{settings.PVE_PORT}/api2/json/nodes/{node}/qemu/{vmid}/vncwebsocket?"
        f"port={port}&vncticket={clean_ticket}"
    )

    pve_ws = None
    try:
        pve_ws = await websockets.connect(
            pve_ws_url,
            ssl=pve_ssl_context,
            subprotocols=['binary'],
            additional_headers=headers
        )

        await websocket.accept()
        
        async def pve_to_client():
            try:
                async for message in pve_ws:
                    await websocket.send_bytes(message if isinstance(message, bytes) else message.encode())
            except:
                pass

        async def client_to_pve():
            try:
                while True:
                    data = await websocket.receive_bytes()
                    await pve_ws.send(data)
            except:
                pass

        await asyncio.gather(pve_to_client(), client_to_pve())

    except Exception as e:
        print(f"VNC Proxy Error: {e}")
        await websocket.close()
    finally:
        if pve_ws:
            await pve_ws.close()
