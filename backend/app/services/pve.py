from proxmoxer import ProxmoxAPI
from app.core.config import settings
import urllib3
import ssl

# Disable SSL warnings if verify is false
if not settings.PVE_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PVEService:
    def __init__(self):
        self.proxmox = ProxmoxAPI(
            settings.PVE_HOST,
            user=settings.PVE_USER,
            token_name=settings.PVE_TOKEN_NAME,
            token_value=settings.PVE_TOKEN_VALUE,
            verify_ssl=settings.PVE_VERIFY_SSL
        )

    def get_cluster_status(self):
        return self.proxmox.cluster.status.get()
    
    def get_cluster_resources(self):
        return self.proxmox.cluster.resources.get()

    def get_nodes(self):
        return self.proxmox.nodes.get()

    def get_node_status(self, node: str):
        return self.proxmox.nodes(node).status.get()

    def get_vms(self, node: str = None):
        if node:
            return self.proxmox.nodes(node).qemu.get()
        else:
            # Aggregate from all nodes
            vms = []
            for n in self.get_nodes():
                # Only check online nodes to avoid errors
                if n.get('status') == 'online':
                    try:
                        node_vms = self.proxmox.nodes(n['node']).qemu.get()
                        for vm in node_vms:
                            vm['node'] = n['node'] # Add node info
                        vms.extend(node_vms)
                    except Exception:
                        continue
            return vms

    def get_vm_status(self, node: str, vmid: int):
        return self.proxmox.nodes(node).qemu(vmid).status.current.get()

    def is_vm_template(self, node: str, vmid: int) -> bool:
        try:
            config = self.proxmox.nodes(node).qemu(vmid).config.get()
        except Exception:
            return False
        return bool(config.get('template'))

    def get_vm_ostype(self, node: str, vmid: int) -> str:
        try:
            config = self.proxmox.nodes(node).qemu(vmid).config.get()
            return config.get('ostype', 'other')
        except Exception:
            return 'other'

    def get_vm_ip(self, node: str, vmid: int):
        try:
            data = self.proxmox.nodes(node).qemu(vmid).agent.post('network-get-interfaces')
        except Exception:
            return None

        result = None
        if isinstance(data, dict):
            if 'result' in data:
                result = data.get('result') or []
            elif 'data' in data and isinstance(data['data'], dict):
                result = data['data'].get('result') or []
        if not result:
            return None

        for iface in result:
            if iface.get('name') == 'lo':
                continue
            for addr in iface.get('ip-addresses', []):
                if addr.get('ip-address-type') == 'ipv4':
                    ip = addr.get('ip-address')
                    if ip and not ip.startswith('127.'):
                        return ip
        return None

    def clone_vm(self, node: str, vmid: int, newid: int, name: str, target_node: str = None):
        # Clone from template
        params = {
            'newid': newid,
            'name': name,
            'full': 0
        }
        if target_node:
            params['target'] = target_node
            
        return self.proxmox.nodes(node).qemu(vmid).clone.post(**params)

    def start_vm(self, node: str, vmid: int):
        return self.proxmox.nodes(node).qemu(vmid).status.start.post()

    def stop_vm(self, node: str, vmid: int):
        return self.proxmox.nodes(node).qemu(vmid).status.stop.post()
        
    def shutdown_vm(self, node: str, vmid: int):
        return self.proxmox.nodes(node).qemu(vmid).status.shutdown.post()

    def reset_vm(self, node: str, vmid: int):
        return self.proxmox.nodes(node).qemu(vmid).status.reset.post()

    def delete_vm(self, node: str, vmid: int):
        return self.proxmox.nodes(node).qemu(vmid).delete()

    def get_vnc_ticket(self, node: str, vmid: int):
        # generate-password=1 is crucial for noVNC
        return self.proxmox.nodes(node).qemu(vmid).vncproxy.post(websocket=1, **{'generate-password': 1})
        
    def get_next_vmid(self):
        return self.proxmox.cluster.nextid.get()

pve_service = PVEService()
