"""Capability-minimising coordinator for the agent-like analytics UX."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import time
from typing import Any, Dict, List

@dataclass
class SpecialistEvent:
    specialist: str; status: str; started_at: str; completed_at: str = ""; duration_ms: float = 0; summary: str = ""
    def to_dict(self): return asdict(self)

class Coordinator:
    def select_capabilities(self, request: str) -> List[str]:
        q = request.lower(); selected = ["profiling"]
        if any(x in q for x in ("quality", "wrong", "missing", "outlier")): selected.append("eda")
        if any(x in q for x in ("forecast", "predict")): selected.append("forecasting")
        if any(x in q for x in ("evidence", "document", "claim")): selected.append("retrieval")
        return selected
    def run_timeline(self, request: str) -> List[Dict[str, Any]]:
        events=[]
        for capability in self.select_capabilities(request):
            start=datetime.now(timezone.utc).isoformat(); tick=time.perf_counter()
            events.append(SpecialistEvent(capability, "completed", start, datetime.now(timezone.utc).isoformat(), round((time.perf_counter()-tick)*1000,2), "Selected for this request.").to_dict())
        return events
