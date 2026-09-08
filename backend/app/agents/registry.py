"""Small registry for in-process specialist capabilities."""
from typing import Any, Dict, List

class SpecialistRegistry:
    def __init__(self): self._items: Dict[str, Any] = {}
    def register(self, specialist: Any) -> Any: self._items[specialist.name] = specialist; return specialist
    def get(self, name: str) -> Any: return self._items.get(name)
    def list(self) -> List[Any]: return list(self._items.values())
    def find_by_capability(self, capability: str) -> List[Any]: return [x for x in self._items.values() if capability in getattr(x, "capabilities", [])]
