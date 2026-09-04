"""Document Parsing Agent for TrustLens"""
import re
from typing import Any, Dict, List
from app.agents.base import BaseAgent


class DocumentParsingAgent(BaseAgent):
    """
    Parses vendor security questionnaires, policy documents, and self-attestations
    into structured security control assertions.
    """

    def __init__(self):
        super().__init__(
            name="Document Parsing Agent",
            role="Extracts structured security assertions from vendor policies and questionnaires",
            category="Worker"
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vendor_profile = state.get("vendor_profile", {})
        attestations = vendor_profile.get("self_attestations", {})
        raw_documents = state.get("documents_text", "")

        parsed_controls: List[Dict[str, str]] = []

        # 1. Parse structured self-attestations
        for category, detail in attestations.items():
            parsed_controls.append({
                "category": category,
                "statement": str(detail),
                "source": f"Vendor Self-Attestation ({vendor_profile.get('name')})",
                "confidence": 0.95
            })

        # 2. Parse any raw document or questionnaire text if provided
        if raw_documents:
            lines = [line.strip() for line in raw_documents.split("\n") if line.strip()]
            for line in lines:
                if ":" in line or "-" in line:
                    parts = re.split(r"[:\-]", line, maxsplit=1)
                    if len(parts) == 2:
                        parsed_controls.append({
                            "category": parts[0].strip().lower().replace(" ", "_"),
                            "statement": parts[1].strip(),
                            "source": "Uploaded Questionnaire / Policy",
                            "confidence": 0.88
                        })

        state["parsed_controls"] = parsed_controls
        return {"parsed_controls": parsed_controls}
