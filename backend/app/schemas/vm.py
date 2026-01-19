from typing import Optional, List
from pydantic import BaseModel

class VMBase(BaseModel):
    vmid: int
    node: str
    name: str

class VMCreate(VMBase):
    owner_id: int

class VMImport(BaseModel):
    vmid: int
    node: str
    name: str
    owner_id: int

class VM(VMBase):
    id: Optional[int] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True

# Extended Schema for returning PVE details + DB details
class VMDetail(VM):
    status: str
    cpu: float = 0
    maxmem: int = 0
    uptime: int = 0
    template: bool = False
    ip: Optional[str] = None
    # Sync status: 'ok', 'orphan' (pve only), 'missing' (db only)
    sync_status: str = 'ok' 
