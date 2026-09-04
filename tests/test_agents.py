"""Automated tests for TrustLens Multi-Agent Extension"""
import sys
import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.agents.ingestion import VendorIngestionAgent
from app.agents.parsing import DocumentParsingAgent
from app.agents.compliance import ComplianceMappingAgent
from app.agents.scoring import RiskScoringAgent
from app.agents.orchestrator import AgentOrchestrator
from app.agents.qa_bot import UserQAAgent

client = TestClient(app)


def test_vendor_ingestion_benchmark():
    agent = VendorIngestionAgent()
    state = {"vendor": {"id": "snowflake"}}
    result = asyncio.run(agent.execute(state))
    profile = result["vendor_profile"]
    assert profile["name"] == "Snowflake Data Cloud"
    assert "encryption_at_rest" in profile["self_attestations"]
    assert len(state["agent_traces"]) == 1
    assert state["agent_traces"][0]["status"] == "success"


def test_document_parsing():
    agent = DocumentParsingAgent()
    state = {
        "vendor_profile": {
            "name": "Acme Security",
            "self_attestations": {"data_isolation": "Dedicated VPC with private subnets"}
        },
        "documents_text": "disaster_recovery: 4-hour RTO across secondary region"
    }
    result = asyncio.run(agent.execute(state))
    controls = result["parsed_controls"]
    assert len(controls) >= 2
    statements = [c["statement"] for c in controls]
    assert any("Dedicated VPC" in s for s in statements)


def test_compliance_mapping():
    agent = ComplianceMappingAgent()
    state = {
        "vendor_profile": {"name": "Test Vendor"},
        "parsed_controls": [
            {"statement": "All persistent storage uses AES-256 encryption at rest"},
            {"statement": "TLS 1.3 enforced for all external transit connections"},
            {"statement": "MFA, RBAC, and SCIM access controls implemented"}
        ],
        "evidence_documents": []
    }
    result = asyncio.run(agent.execute(state))
    findings = result["compliance_findings"]
    assert len(findings) > 0
    frameworks = {f["framework"] for f in findings}
    assert "SOC 2 Type II" in frameworks
    assert "ISO 27001:2022" in frameworks
    assert "NIST CSF v2.0" in frameworks
    assert result["compliance_rate"] > 0.0


def test_risk_scoring():
    agent = RiskScoringAgent()
    state = {
        "vendor_profile": {
            "data_tier": "Tier 1 (Critical)",
            "inherent_risk": "High",
            "external_signals": {
                "security_rating": 95,
                "recent_breaches": 0,
                "cve_critical_count": 0
            }
        },
        "compliance_rate": 90.0
    }
    result = asyncio.run(agent.execute(state))
    score = result["risk_score"]
    assert 0.0 <= score <= 100.0
    assert result["risk_tier"] in ["Low", "Moderate", "High", "Critical"]


def test_orchestrator_assessment():
    orchestrator = AgentOrchestrator()
    result = asyncio.run(orchestrator.run_assessment(
        vendor_data={"id": "datadog"},
        query="Verify encryption and APM telemetry data isolation"
    ))
    assert "vendor_profile" in result
    assert "compliance_findings" in result
    assert "risk_assessment" in result
    assert "qa_verification" in result
    assert len(result["agent_traces"]) >= 5
    assert result["total_latency_ms"] > 0


def test_api_assess_endpoint():
    payload = {
        "vendor": {
            "id": "stripe"
        },
        "query": "Evaluate PCI-DSS compliance and cardholder data encryption"
    }
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["vendor_profile"]["name"] == "Stripe Payments"
    assert data["risk_assessment"]["risk_tier"] in ["Low", "Moderate", "High", "Critical"]
    assert len(data["agent_traces"]) > 0


def test_api_ask_endpoint():
    payload = {
        "vendor": {
            "name": "Stripe",
            "data_tier": "Tier 1 (Critical)",
            "self_attestations": {
                "encryption_at_rest": "AES-256 PCI-DSS tokenization vault"
            }
        },
        "question": "What encryption standard is used for data at rest?"
    }
    response = client.post("/api/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
