"""Vendor Ingestion Agent for TrustLens"""
from typing import Any, Dict
from app.agents.base import BaseAgent

PRECONFIGURED_VENDORS = {
    "snowflake": {
        "vendor_id": "vnd_snowflake",
        "name": "Snowflake Data Cloud",
        "domain": "snowflake.com",
        "industry": "Cloud Data Warehousing",
        "data_tier": "Tier 1 (Critical)",
        "inherent_risk": "High",
        "data_classified": ["Customer Analytics", "PII", "Financial Records"],
        "self_attestations": {
            "encryption_at_rest": "AES-256 with customer-managed keys (Tri-Secret Secure)",
            "encryption_in_transit": "TLS 1.3 enforced for all client and inter-node sessions",
            "access_control": "MFA, SCIM provisioning, and role-based access control (RBAC)",
            "soc2_type2": "Certified with clean SOC 2 Type II audit report",
            "incident_response": "24/7 CSIRT with 1-hour SLA for critical severity security incidents",
            "disaster_recovery": "Multi-region failover across AWS, Azure, and Google Cloud"
        },
        "external_signals": {
            "security_rating": 94,
            "recent_breaches": 0,
            "cve_critical_count": 0,
            "last_audit_date": "2026-05-15"
        }
    },
    "datadog": {
        "vendor_id": "vnd_datadog",
        "name": "Datadog Observability",
        "domain": "datadoghq.com",
        "industry": "Cloud Monitoring & APM",
        "data_tier": "Tier 2 (High)",
        "inherent_risk": "Medium",
        "data_classified": ["Infrastructure Telemetry", "Application Logs", "APM Traces"],
        "self_attestations": {
            "encryption_at_rest": "AES-256 for all persistent storage volumes and logs",
            "encryption_in_transit": "TLS 1.2+ for telemetry ingestion APIs and UI access",
            "access_control": "SAML 2.0 SSO, Google Auth, and granular RBAC permissions",
            "soc2_type2": "Compliant with SOC 2 Type II and ISO 27001 certifications",
            "incident_response": "Documented incident response framework with automated paging",
            "disaster_recovery": "Redundant multi-zone availability architecture"
        },
        "external_signals": {
            "security_rating": 91,
            "recent_breaches": 0,
            "cve_critical_count": 1,
            "last_audit_date": "2026-04-10"
        }
    },
    "stripe": {
        "vendor_id": "vnd_stripe",
        "name": "Stripe Payments",
        "domain": "stripe.com",
        "industry": "Financial Infrastructure & Payments",
        "data_tier": "Tier 1 (Critical)",
        "inherent_risk": "High",
        "data_classified": ["Cardholder Data", "Bank Account Info", "Payment Tokens"],
        "self_attestations": {
            "encryption_at_rest": "PCI-DSS Level 1 certified tokenization vault with AES-256",
            "encryption_in_transit": "Strict HTTPS HSTS TLS 1.3 only",
            "access_control": "Zero Trust network architecture with hardware security keys (FIDO2)",
            "soc2_type2": "SOC 1, SOC 2 Type II, and PCI-DSS Level 1 certified",
            "incident_response": "Dedicated 24/7 Security Operations Center with real-time alerting",
            "disaster_recovery": "Fully autonomous multi-cloud and multi-region resilience"
        },
        "external_signals": {
            "security_rating": 98,
            "recent_breaches": 0,
            "cve_critical_count": 0,
            "last_audit_date": "2026-06-20"
        }
    }
}


class VendorIngestionAgent(BaseAgent):
    """
    Ingests and normalizes vendor metadata, data classification, and baseline tiers.
    """

    def __init__(self):
        super().__init__(
            name="Vendor Ingestion Agent",
            role="Normalizes vendor profile, tiering, and external security ratings",
            category="Worker"
        )

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vendor_input = state.get("vendor", {})
        vendor_id = vendor_input.get("id", "").lower().strip()

        # Check if pre-configured benchmark vendor
        if vendor_id in PRECONFIGURED_VENDORS:
            vendor_profile = dict(PRECONFIGURED_VENDORS[vendor_id])
            # Override with any custom user inputs provided
            for k, v in vendor_input.items():
                if v:
                    vendor_profile[k] = v
        else:
            # Custom vendor dynamic ingestion
            name = vendor_input.get("name", "Custom Vendor")
            domain = vendor_input.get("domain", "vendor.internal")
            industry = vendor_input.get("industry", "Software & Technology")
            data_tier = vendor_input.get("data_tier", "Tier 2 (High)")

            vendor_profile = {
                "vendor_id": vendor_id or f"vnd_{name.lower().replace(' ', '_')}",
                "name": name,
                "domain": domain,
                "industry": industry,
                "data_tier": data_tier,
                "inherent_risk": "Medium" if "Tier 2" in data_tier else "High",
                "data_classified": vendor_input.get("data_classified", ["Internal Operational Data"]),
                "self_attestations": vendor_input.get("self_attestations", {
                    "encryption_at_rest": "AES-256 standard encryption",
                    "encryption_in_transit": "TLS 1.2+ encrypted protocols",
                    "access_control": "Role-based access controls and password policies",
                    "soc2_type2": "Self-attested compliance with industry best practices",
                    "incident_response": "Standard internal security response procedures"
                }),
                "external_signals": {
                    "security_rating": int(vendor_input.get("security_rating", 85)),
                    "recent_breaches": int(vendor_input.get("recent_breaches", 0)),
                    "cve_critical_count": int(vendor_input.get("cve_critical_count", 0)),
                    "last_audit_date": "2026-01-15"
                }
            }

        state["vendor_profile"] = vendor_profile
        return {"vendor_profile": vendor_profile}
