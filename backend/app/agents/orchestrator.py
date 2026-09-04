"""Central Multi-Agent Orchestrator for TrustLens"""
import asyncio
import time
import logging
from typing import Any, Dict

from app.agents.ingestion import VendorIngestionAgent
from app.agents.parsing import DocumentParsingAgent
from app.agents.retrieval import EvidenceRetrievalAgent
from app.agents.compliance import ComplianceMappingAgent
from app.agents.scoring import RiskScoringAgent
from app.agents.report import FindingsReportAgent
from app.agents.qa_verifier import QualityAssuranceAgent
from app.agents.qa_bot import UserQAAgent

logger = logging.getLogger("trustlens.orchestrator")


class AgentOrchestrator:
    """
    Coordinates multi-agent workflow for comprehensive third-party vendor risk assessment.
    Executes worker agents in dependency sequence, maintains shared state, and
    compiles end-to-end execution traces and digital audit signatures.
    """

    def __init__(self):
        self.ingestion_agent = VendorIngestionAgent()
        self.parsing_agent = DocumentParsingAgent()
        self.retrieval_agent = EvidenceRetrievalAgent()
        self.compliance_agent = ComplianceMappingAgent()
        self.scoring_agent = RiskScoringAgent()
        self.report_agent = FindingsReportAgent()
        self.qa_agent = QualityAssuranceAgent()
        self.user_qa_agent = UserQAAgent()

    async def run_assessment(self, vendor_data: Dict[str, Any], query: str = "", documents_text: str = "") -> Dict[str, Any]:
        """
        Full 6-stage multi-agent assessment pipeline.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Multi-Agent assessment for vendor: %s", vendor_data.get("name", "Unknown"))

        state: Dict[str, Any] = {
            "vendor": vendor_data,
            "query": query,
            "documents_text": documents_text,
            "agent_traces": []
        }

        # Stage 1: Vendor Ingestion
        await self.ingestion_agent.execute(state)

        # Stage 2: Parsing and Semantic Vector Retrieval (can run concurrently)
        await asyncio.gather(
            self.parsing_agent.execute(state),
            self.retrieval_agent.execute(state)
        )

        # Stage 3: Compliance Framework Mapping
        await self.compliance_agent.execute(state)

        # Stage 4: Quantitative Risk Scoring
        await self.scoring_agent.execute(state)

        # Stage 5: Findings Report Generation (OpenAI grounded narrative)
        await self.report_agent.execute(state)

        # Stage 6: Quality Assurance & Claim Verification (Truth Guard)
        await self.qa_agent.execute(state)

        total_duration_ms = round((time.perf_counter() - start_time) * 1000, 1)

        return {
            "vendor_profile": state.get("vendor_profile", {}),
            "parsed_controls": state.get("parsed_controls", []),
            "compliance_findings": state.get("compliance_findings", []),
            "compliance_rate": state.get("compliance_rate", 0.0),
            "risk_assessment": state.get("risk_assessment", {}),
            "report_narrative": state.get("report_narrative", ""),
            "qa_verification": state.get("qa_verification", {}),
            "evidence_documents": state.get("evidence_documents", []),
            "agent_traces": state.get("agent_traces", []),
            "total_latency_ms": total_duration_ms
        }

    async def answer_analyst_question(self, vendor_profile: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Delegate to UserQAAgent for ad-hoc analyst queries.
        """
        return await self.user_qa_agent.answer_question(vendor_profile, question)
