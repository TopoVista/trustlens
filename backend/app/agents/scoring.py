"""Quantitative Risk Scoring Agent for TrustLens"""
from typing import Any, Dict
from app.agents.base import BaseAgent


class RiskScoringAgent(BaseAgent):
    """
    Computes objective quantitative risk scores (0-100), residual risk tiering,
    and governance recommendations based on multi-factor telemetry.
    """

    def __init__(self):
        super().__init__(
            name="Risk Scoring Agent",
            role="Calculates multi-factor risk scores, residual risk tiers, and impact ratings",
            category="Worker"
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vendor_profile = state.get("vendor_profile", {})
        compliance_rate = state.get("compliance_rate", 80.0)
        ext_signals = vendor_profile.get("external_signals", {})

        sec_rating = ext_signals.get("security_rating", 85)
        breaches = ext_signals.get("recent_breaches", 0)
        cve_count = ext_signals.get("cve_critical_count", 0)
        tier_str = vendor_profile.get("data_tier", "Tier 2 (High)")

        # 1. Base vulnerability factor (inverse of security rating, 0 to 40 pts)
        security_penalty = max(0.0, (100 - sec_rating) * 0.4)

        # 2. Compliance gap penalty (0 to 35 pts)
        compliance_penalty = max(0.0, (100 - compliance_rate) * 0.35)

        # 3. Threat intelligence / Incident penalty (0 to 25 pts)
        incident_penalty = min(25.0, (breaches * 15.0) + (cve_count * 5.0))

        # Raw risk score (0 = Perfect, 100 = Extremely Hazardous)
        raw_score = round(security_penalty + compliance_penalty + incident_penalty, 1)

        # Data classification multiplier
        if "Tier 1" in tier_str or "Critical" in tier_str:
            raw_score = min(100.0, raw_score * 1.15)

        risk_score = round(min(100.0, max(0.0, raw_score)), 1)

        # Determine risk tier
        if risk_score < 20:
            tier = "Low"
            recommendation = "Approved for standard vendor onboarding. Annual continuous monitoring."
        elif risk_score < 45:
            tier = "Moderate"
            recommendation = "Approved with standard mitigations. Periodic audit check-ins every 6 months."
        elif risk_score < 70:
            tier = "High"
            recommendation = "Conditional approval requires remediation of identified control gaps within 60 days."
        else:
            tier = "Critical"
            recommendation = "High risk detected. Vendor engagement escalation required before data transfer."

        result = {
            "risk_score": risk_score,
            "risk_tier": tier,
            "inherent_risk": vendor_profile.get("inherent_risk", "Medium"),
            "residual_risk": tier,
            "factors": {
                "security_rating": sec_rating,
                "compliance_score": compliance_rate,
                "breach_count": breaches,
                "critical_cves": cve_count
            },
            "recommendation": recommendation
        }

        state["risk_assessment"] = result
        return result
