"""Timeline Specialist for TrustLens"""
import re
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist


class TimelineAgent(BaseSpecialist):
    """
    Extracts chronological dates, temporal references, and milestones from workspace content
    and organizes them into an ordered timeline with direct evidence citations.
    """

    def __init__(self):
        super().__init__(
            name="Timeline Specialist",
            description="Extracts chronological events, years, and dates into an evidence-linked timeline",
            capabilities=["event_extraction", "chronology_mapping", "temporal_ordering"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context.get("text", "")
        doc_id = context.get("document_id")

        if not text.strip():
            return {"events": []}

        # Date regex: YYYY-MM-DD, Month YYYY, or standalone 20XX
        pattern = r"\b((?:19|20)\d{2}(?:[-/.](?:0[1-9]|1[0-2])(?:[-/.](?:0[1-9]|[12]\d|3[01]))?)?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2})\b"

        sentences = re.split(r"[.!?]\s+", text)
        events: List[Dict[str, Any]] = []

        for s in sentences:
            matches = re.findall(pattern, s)
            if matches:
                date_str = matches[0].strip()
                # Clean up title
                title = s.strip()
                if len(title) > 90:
                    title = title[:87] + "..."

                # Approximate numeric timestamp for sorting
                year_match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
                timestamp_val = float(year_match.group(1)) if year_match else 2024.0

                events.append({
                    "title": title,
                    "date_str": date_str,
                    "timestamp_val": timestamp_val,
                    "description": s.strip(),
                    "document_id": doc_id,
                    "workspace_id": workspace_id
                })

        # Sort chronologically
        events.sort(key=lambda e: e["timestamp_val"])
        return {"events": events, "count": len(events)}
