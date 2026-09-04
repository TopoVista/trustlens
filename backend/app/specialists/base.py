"""Base Specialist Interface for TrustLens Reasoning Engine"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger("trustlens.specialists")


class BaseSpecialist(ABC):
    """
    Abstract interface for specialized reasoning capabilities.
    Specialists are reasoning modules—not chatbot personas.
    """

    def __init__(self, name: str, description: str, capabilities: List[str]):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.logger = logging.getLogger(f"trustlens.specialist.{name.lower().replace(' ', '_')}")

    @abstractmethod
    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes specialized reasoning over workspace-scoped context.
        """
        raise NotImplementedError
