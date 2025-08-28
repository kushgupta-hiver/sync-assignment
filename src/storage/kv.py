from abc import ABC, abstractmethod
from typing import Optional


class KeyValueStore(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        raise NotImplementedError

