"""Document Comparison Specialist for TrustLens"""
import re
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist


class DocumentComparisonAgent(BaseSpecialist):
    """
    Substantive Document Comparison Specialist:
    Goes beyond raw text diffs to analyze WHAT CHANGED, WHY IT MATTERS,
    the supporting EVIDENCE, and POTENTIAL IMPACT across versions or documents.
    """

    def __init__(self):
        super().__init__(
            name="Document Comparison Specialist",
            description="Performs semantic comparison between documents, identifying changes, impact, and evidence",
            capabilities=["document_comparison", "diff_semantics", "impact_analysis"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        doc_a_text = context.get("doc_a_text", "")
        doc_b_text = context.get("doc_b_text", "")
        title_a = context.get("doc_a_title", "Version A")
        title_b = context.get("doc_b_title", "Version B")

        if not doc_a_text or not doc_b_text:
            return {"differences": [], "summary": "Insufficient text provided for comparison"}

        diffs = self.compare_texts(doc_a_text, doc_b_text, title_a, title_b)
        return {"differences": diffs, "total_differences": len(diffs)}

    def compare_texts(self, text_a: str, text_b: str, title_a: str, title_b: str) -> List[Dict[str, Any]]:
        """Extracts substantive differences in numbers, requirements, or policies."""
        sents_a = [s.strip() for s in re.split(r"[.!?]\s+", text_a) if len(s.strip()) > 20]
        sents_b = [s.strip() for s in re.split(r"[.!?]\s+", text_b) if len(s.strip()) > 20]

        diffs = []

        # Find sentences in B that mention concepts from A with different metrics
        for sa in sents_a:
            nums_a = re.findall(r"\b\d+(?:\.\d+)?%?\b", sa)
            words_a = set(sa.lower().split())
            if not nums_a:
                continue

            for sb in sents_b:
                nums_b = re.findall(r"\b\d+(?:\.\d+)?%?\b", sb)
                words_b = set(sb.lower().split())

                if nums_b and nums_a != nums_b:
                    overlap = (words_a & words_b) - {"the", "and", "with", "this", "that", "from", "were"}
                    if len(overlap) >= 3:
                        diffs.append({
                            "topic": " ".join(list(overlap)[:3]).title(),
                            "what_changed": f"Metric changed from {nums_a[0]} in {title_a} to {nums_b[0]} in {title_b}.",
                            "why_it_matters": "Quantitative baseline has shifted between versions.",
                            "evidence": f"[{title_a}]: \"{sa}\" vs [{title_b}]: \"{sb}\"",
                            "potential_impact": "Operational forecasts, budgets, or SLAs may require recalibration."
                        })
                        break

        # Check for newly introduced requirements
        keywords_req = {"mandatory", "required", "prohibited", "strict", "enforced"}
        for sb in sents_b:
            if any(k in sb.lower() for k in keywords_req) and not any(sb[:25].lower() in sa.lower() for sa in sents_a):
                diffs.append({
                    "topic": "Policy / Requirement Shift",
                    "what_changed": f"New mandatory requirement introduced in {title_b}.",
                    "why_it_matters": "Adds enforceable compliance or operational constraint.",
                    "evidence": f"[{title_b}]: \"{sb}\"",
                    "potential_impact": "Requires immediate operational verification."
                })
                if len(diffs) >= 4:
                    break

        return diffs
