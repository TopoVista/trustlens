"""Compliance Mapping Agent for TrustLens"""
from typing import Any, Dict, List
from app.agents.base import BaseAgent

FRAMEWORK_CONTROLS = [
    {
        "framework": "SOC 2 Type II",
        "control_id": "CC6.1",
        "title": "Logical Access Controls & IAM",
        "requirement": "The entity implements logical access security software, infrastructure, and architectures over protected information assets.",
        "keywords": ["access_control", "mfa", "rbac", "iam", "sso", "fido2"]
    },
    {
        "framework": "SOC 2 Type II",
        "control_id": "CC6.6",
        "title": "Boundary Protection & Cryptography",
        "requirement": "The entity implements boundary protection and encrypts data at rest and in transit across public and internal networks.",
        "keywords": ["encryption", "aes-256", "tls", "https", "at_rest", "transit"]
    },
    {
        "framework": "SOC 2 Type II",
        "control_id": "CC7.1",
        "title": "Vulnerability Management & Detection",
        "requirement": "The entity uses vulnerability scanning and patch management to detect potential security anomalies and vulnerabilities.",
        "keywords": ["vulnerability", "cve", "scan", "patch", "audit"]
    },
    {
        "framework": "ISO 27001:2022",
        "control_id": "A.5.15",
        "title": "Access Control Management",
        "requirement": "Access to physical and logical assets shall be managed and restricted according to the established access control policy.",
        "keywords": ["access_control", "rbac", "permissions", "scim", "sso"]
    },
    {
        "framework": "ISO 27001:2022",
        "control_id": "A.8.24",
        "title": "Use of Cryptography",
        "requirement": "Rules for the effective use of cryptography, including key management, shall be defined and implemented.",
        "keywords": ["encryption", "aes", "keys", "tls", "cryptography"]
    },
    {
        "framework": "NIST CSF v2.0",
        "control_id": "PR.DS-01",
        "title": "Data-at-Rest Protection",
        "requirement": "Confidentiality, integrity, and availability of data at rest are protected by robust cryptographic algorithms.",
        "keywords": ["encryption_at_rest", "aes-256", "vault", "storage"]
    },
    {
        "framework": "NIST CSF v2.0",
        "control_id": "PR.DS-02",
        "title": "Data-in-Transit Protection",
        "requirement": "Data in transit is protected using modern, secure communication protocols and mutual authentication.",
        "keywords": ["encryption_in_transit", "tls 1.3", "tls 1.2", "https"]
    },
    {
        "framework": "NIST CSF v2.0",
        "control_id": "DE.CM-01",
        "title": "Continuous Network & Log Monitoring",
        "requirement": "The network environment and systems are monitored continuously to detect potential cybersecurity events.",
        "keywords": ["monitoring", "csirt", "soc", "apm", "logging", "incident_response"]
    }
]


class ComplianceMappingAgent(BaseAgent):
    """
    Maps vendor assertions and evidence to standardized compliance controls (SOC 2, ISO 27001, NIST CSF).
    """

    def __init__(self):
        super().__init__(
            name="Compliance Mapping Agent",
            role="Maps vendor evidence against SOC 2, ISO 27001, and NIST CSF security controls",
            category="Worker"
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        parsed_controls = state.get("parsed_controls", [])
        evidence_docs = state.get("evidence_documents", [])
        vendor_profile = state.get("vendor_profile", {})

        all_text = " ".join([c["statement"] for c in parsed_controls]).lower()
        if evidence_docs:
            all_text += " " + " ".join([d.get("text", "") for d in evidence_docs]).lower()

        mapped_findings: List[Dict[str, Any]] = []
        satisfied_count = 0

        for ctrl in FRAMEWORK_CONTROLS:
            matched_keywords = [kw for kw in ctrl["keywords"] if kw in all_text]
            
            if len(matched_keywords) >= 2 or (len(matched_keywords) == 1 and ("aes-256" in matched_keywords or "tls" in matched_keywords)):
                status = "Satisfied"
                confidence = 0.92
                satisfied_count += 1
                evidence_excerpt = next(
                    (c["statement"] for c in parsed_controls if any(kw in c["statement"].lower() for kw in matched_keywords)),
                    "Vendor self-attestation matches control standards."
                )
            elif len(matched_keywords) == 1:
                status = "Partial"
                confidence = 0.72
                evidence_excerpt = "Partial control evidence detected; further audit documentation recommended."
            else:
                status = "Gap"
                confidence = 0.85
                evidence_excerpt = "No verifiable control policy identified in vendor disclosures."

            mapped_findings.append({
                "framework": ctrl["framework"],
                "control_id": ctrl["control_id"],
                "title": ctrl["title"],
                "requirement": ctrl["requirement"],
                "status": status,
                "confidence": confidence,
                "matched_evidence": evidence_excerpt,
                "vendor_name": vendor_profile.get("name", "Vendor")
            })

        compliance_rate = round((satisfied_count / len(FRAMEWORK_CONTROLS)) * 100, 1) if FRAMEWORK_CONTROLS else 0.0

        state["compliance_findings"] = mapped_findings
        state["compliance_rate"] = compliance_rate
        return {
            "compliance_findings": mapped_findings,
            "compliance_rate": compliance_rate,
            "total_controls_evaluated": len(FRAMEWORK_CONTROLS)
        }
