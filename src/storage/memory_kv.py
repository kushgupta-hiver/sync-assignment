from typing import Optional
from threading import RLock


class InMemoryKV:
    def __init__(self):
        self._store = {}
        self._lock = RLock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._store[key] = value

