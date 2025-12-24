from dataclasses import dataclass
from enum import Enum

class DriftState(Enum):
    IN_SYNC = "IN_SYNC"
    REMOTE_AHEAD = "REMOTE_AHEAD"
    LOCAL_AHEAD = "LOCAL_AHEAD"
    DIVERGED = "DIVERGED"
    UNKNOWN = "UNKNOWN"

@dataclass
class DriftReport:
    state: DriftState
    local_hash: str
    remote_hash: str
    last_synced_at: str

def calculate_drift(local_hash: str, remote_hash: str, last_synced_hash: str = None) -> DriftState:
    if local_hash == remote_hash:
        return DriftState.IN_SYNC
    
    if last_synced_hash:
        if local_hash == last_synced_hash and remote_hash != last_synced_hash:
            return DriftState.REMOTE_AHEAD
        if remote_hash == last_synced_hash and local_hash != last_synced_hash:
            return DriftState.LOCAL_AHEAD
            
    return DriftState.DIVERGED
