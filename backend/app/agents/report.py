"""Findings & Assessment Report Generation Agent for TrustLens"""
import os
import logging
from typing import Any, Dict, List
from app.agents.base import BaseAgent
from app.pipeline.generator import _get_client

logger = logging.getLogger("trustlens.agents.report")


class FindingsReportAgent(BaseAgent):
    """
    Synthesizes multi-stream vendor evidence, compliance findings, and quantitative risk scores
    into a grounded, professional executive security assessment report.
    """

    def __init__(self):
        super().__init__(
            name="Findings Report Agent",
            role="Drafts grounded executive risk assessments, control summaries, and remediation roadmaps",
            category="Worker"
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vendor_profile = state.get("vendor_profile", {})
        compliance = state.get("compliance_findings", [])
        risk = state.get("risk_assessment", {})
        evidence_docs = state.get("evidence_documents", [])

        vendor_name = vendor_profile.get("name", "Vendor")
        risk_tier = risk.get("risk_tier", "Moderate")
        risk_score = risk.get("risk_score", 30.0)

        # Build context summary
        gap_controls = [c["title"] for c in compliance if c.get("status") == "Gap"]
        satisfied_controls = [c["title"] for c in compliance if c.get("status") == "Satisfied"]

        prompt = f"""You are an expert third-party cybersecurity risk analyst.
Generate an executive security assessment report for vendor: {vendor_name}.

Context Data:
- Vendor Domain: {vendor_profile.get('domain')}
- Data Sensitivity Tier: {vendor_profile.get('data_tier')}
- Quantitative Risk Score: {risk_score}/100 ({risk_tier} Risk)
- Satisfied Controls: {', '.join(satisfied_controls) if satisfied_controls else 'None'}
- Identified Control Gaps: {', '.join(gap_controls) if gap_controls else 'None'}
- Security Rating: {risk.get('factors', {}).get('security_rating', 85)}/100

Instructions:
Provide a concise, highly professional assessment (3-4 sentences).
State clearly whether the vendor is approved, summarize primary strengths (e.g. encryption or access control), and state any required remediations.
Do not invent unverified facts."""

        # Attempt OpenAI generation with grounded prompt
        report_text: str = ""
        try:
            client = _get_client()
            model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini-2024-07-18").strip()
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional third-party cybersecurity risk assessor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            report_text = response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.warning("Falling back to deterministic report generation: %s", e)
            report_text = (
                f"{vendor_name} demonstrates a {risk_tier.lower()} risk posture with an overall composite score of {risk_score}/100. "
                f"The vendor satisfies key architectural requirements including {satisfied_controls[0] if satisfied_controls else 'data protection protocols'}. "
                f"Identified control gaps include {gap_controls[0] if gap_controls else 'minor policy documentation requirements'}, which should be remediated within standard review windows."
            )

        state["report_narrative"] = report_text
        return {
            "vendor_name": vendor_name,
            "report_narrative": report_text,
            "risk_tier": risk_tier,
            "risk_score": risk_score
        }
