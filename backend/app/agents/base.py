"""Base Agent abstraction for TrustLens Multi-Agent Architecture"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger("trustlens.agents")


class BaseAgent(ABC):
    """
    Abstract base class for all TrustLens specialized agents.
    Enforces standardized execution, telemetry logging, and status reporting.
    """

    def __init__(self, name: str, role: str, category: str = "Worker"):
        self.name = name
        self.role = role
        self.category = category  # Worker, Service, or Support
        self.logger = logging.getLogger(f"trustlens.agent.{name.lower().replace(' ', '_')}")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper that measures execution duration, catches errors, and logs telemetry.
        """
        start_time = time.perf_counter()
        self.logger.info("Starting execution of agent: %s [%s]", self.name, self.role)
        status = "success"
        error_msg: Optional[str] = None
        result: Dict[str, Any] = {}

        try:
            result = await self.run(state)
        except Exception as e:
            status = "failed"
            error_msg = str(e)
            self.logger.error("Error in agent %s: %s", self.name, error_msg, exc_info=True)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            trace = {
                "agent": self.name,
                "role": self.role,
                "category": self.category,
                "status": status,
                "duration_ms": duration_ms,
                "error": error_msg
            }
            # Append execution trace into system state
            if "agent_traces" not in state:
                state["agent_traces"] = []
            state["agent_traces"].append(trace)
            self.logger.info("Completed %s in %.1f ms (status: %s)", self.name, duration_ms, status)

        return result

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core domain logic for the specialized agent.
        """
        raise NotImplementedError("Subclasses must implement run()")
