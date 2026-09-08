from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class ToolDescriptor:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    permissions: str = "read_only"
