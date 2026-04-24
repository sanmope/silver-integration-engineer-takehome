import json
from pathlib import Path
from filelock import FileLock


class SyncStatus:
    def __init__(self, path: str = "sync_status.json"):
        self._path = Path(path)

    def update(self, integration_id: str, **kwargs) -> None:
        lock = FileLock(str(self._path) + ".lock")
        with lock:
            all_status = {}
            if self._path.exists():
                all_status = json.loads(self._path.read_text())
            
            current = all_status.get(integration_id, {})
            current.update(kwargs)
            all_status[integration_id] = current

        #Atomic Write avoids corruption if process dies in the middle
        tmp = self._path.with_suffix('.tmp')
        tmp.write_text(json.dumps(all_status, default=str))
        tmp.replace(self._path)

    def load(self, integration_id: str) -> dict | None:
        if not self._path.exists():
            return None
        return json.loads(self._path.read_text()).get(integration_id)