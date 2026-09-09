"""Intent-Aware Analysis Planner for TrustLens Knowledge Intelligence"""
import re
import time
import logging
from typing import Any, Dict, List, Optional
from app.planner.registry import AgentRegistry
from app.knowledge.repository import KnowledgeRepository
from app.knowledge.hybrid_retriever import HybridKnowledgeRetriever

logger = logging.getLogger("trustlens.planner")


class AnalysisPlanner:
    """
    Decomposes user questions into a targeted task graph of specialized capabilities.
    Does NOT invoke every agent for every query.
    Generates a transparent analysis trace showing exactly what the system investigated.
    """

    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        self.repo = repo or KnowledgeRepository()
        self.retriever = HybridKnowledgeRetriever(self.repo)
        self.registry = AgentRegistry()

    def classify_intent(self, query: str) -> str:
        q = query.lower()
        if q.startswith("why") or "reason" in q or "cause" in q or "why did" in q:
            return "WHY_ANALYSIS"
        elif "contradict" in q or "conflict" in q or "disagree" in q or "differ" in q:
            return "CONTRADICTION_QUERY"
        elif "missing" in q or "gap" in q or "don't know" in q or "blind spot" in q or "unknown" in q:
            return "GAP_QUERY"
        elif "compare" in q or "difference between" in q or "versus" in q or " vs " in q:
            return "COMPARISON_QUERY"
        elif "pattern" in q or "trend" in q or "anomaly" in q or "what should i know" in q:
            return "DISCOVERY_QUERY"
        else:
            return "FACTUAL_QUERY"

    async def execute_plan(self, workspace_id: str, query: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        intent = self.classify_intent(query)
        logger.info("Executing plan for workspace '%s', intent: %s, query: '%s'", workspace_id, intent, query)

        plan_trace: List[str] = []

        # 1. Base Retrieval
        retrieved_chunks = self.retriever.retrieve(workspace_id, query, k=6)
        plan_trace.append(f"Retrieved {len(retrieved_chunks)} relevant source passages via hybrid search")

        ent_context = " ".join([c["text"] for c in retrieved_chunks])
        semantic_rules = self.repo.get_semantic_rules(workspace_id)
        entities: List[Dict[str, Any]] = []
        claims: List[Dict[str, Any]] = []
        verified_claims: List[Dict[str, Any]] = []

        # 2. Select the smallest useful specialist set. Comparison requests
        # operate on retrieved documents directly; they do not need every
        # extraction and verification specialist to run first.
        if intent in {"WHY_ANALYSIS", "FACTUAL_QUERY", "DISCOVERY_QUERY", "COMPARISON_QUERY"}:
            entity_agent = self.registry.get("entity_agent")
            ent_res = await entity_agent.analyze(
                workspace_id, {"text": ent_context, "semantic_rules": semantic_rules}
            )
            entities = ent_res.get("entities", [])
            if entities:
                plan_trace.append(
                    f"Identified {len(entities)} contextual entities ({', '.join([e['name'] for e in entities[:3]])})"
                )

        if intent != "COMPARISON_QUERY":
            claim_detective = self.registry.get("claim_detective")
            claim_res = await claim_detective.analyze(workspace_id, {"text": ent_context})
            claims = claim_res.get("claims", [])
            plan_trace.append(f"Extracted {len(claims)} atomic assertions")

            evidence_agent = self.registry.get("evidence_agent")
            ev_res = await evidence_agent.analyze(
                workspace_id, {"claims": claims, "candidate_chunks": retrieved_chunks}
            )
            verified_claims = ev_res.get("verified_claims", [])

        # 3. Intent-specific specialist dispatch
        contradictions = []
        knowledge_gaps = []
        events = []
        comparisons = []
        patterns = []

        if intent in {"WHY_ANALYSIS", "CONTRADICTION_QUERY"}:
            contra_agent = self.registry.get("contradiction_agent")
            contra_res = await contra_agent.analyze(workspace_id, {"claims": verified_claims})
            contradictions = contra_res.get("contradictions", [])
            if contradictions:
                plan_trace.append(f"Investigated {len(contradictions)} cross-document discrepancies")

        if intent == "WHY_ANALYSIS":
            timeline_agent = self.registry.get("timeline_agent")
            time_res = await timeline_agent.analyze(workspace_id, {"text": ent_context})
            events = time_res.get("events", [])
            if events:
                plan_trace.append(f"Constructed chronological timeline ({len(events)} temporal anchors)")

        if intent in {"GAP_QUERY", "WHY_ANALYSIS"}:
            gap_agent = self.registry.get("gap_agent")
            gap_res = await gap_agent.analyze(workspace_id, {
                "claims": verified_claims,
                "contradictions": contradictions,
                "events": events
            })
            knowledge_gaps = gap_res.get("knowledge_gaps", [])
            if knowledge_gaps:
                plan_trace.append(f"Audited workspace blind spots ({len(knowledge_gaps)} knowledge gaps)")

        if intent == "COMPARISON_QUERY" and len(retrieved_chunks) >= 2:
            comparison_agent = self.registry.get("comparison_agent")
            first, second = retrieved_chunks[:2]
            comparison_res = await comparison_agent.analyze(workspace_id, {
                "doc_a_text": first.get("text", ""),
                "doc_b_text": second.get("text", ""),
                "doc_a_title": first.get("document_title", "Source A"),
                "doc_b_title": second.get("document_title", "Source B"),
            })
            comparisons = comparison_res.get("differences", [])
            plan_trace.append(f"Compared {len(comparisons)} substantive source differences")

        if intent == "DISCOVERY_QUERY":
            pattern_agent = self.registry.get("pattern_hunter")
            pattern_res = await pattern_agent.analyze(
                workspace_id, {"chunks": retrieved_chunks, "claims": claims}
            )
            patterns = pattern_res.get("patterns", [])
            plan_trace.append(f"Scanned {len(patterns)} cross-document patterns")

        # 5. Synthesis following Phase 11 Answer Contract
        synthesis_agent = self.registry.get("synthesis_agent")
        plan_trace.append("Synthesizing evidence-grounded response with uncertainty preservation")

        synthesis_res = await synthesis_agent.analyze(workspace_id, {
            "query": query,
            "retrieved_chunks": retrieved_chunks,
            "verified_claims": verified_claims,
            "contradictions": contradictions,
            "knowledge_gaps": knowledge_gaps,
            "entities": entities,
            "events": events,
            "comparisons": comparisons,
            "patterns": patterns,
            "semantic_rules": semantic_rules
        })

        total_ms = round((time.perf_counter() - start_time) * 1000, 1)

        related_knowledge = dict(synthesis_res["related_knowledge"])
        if comparisons:
            related_knowledge["comparisons"] = comparisons
        if patterns:
            related_knowledge["patterns"] = patterns

        return {
            "query": query,
            "intent": intent,
            "answer": synthesis_res["answer"],
            "confidence": synthesis_res["confidence"],
            "claims": synthesis_res["claims"],
            "evidence": synthesis_res["evidence"],
            "contradictions": synthesis_res["contradictions"],
            "assumptions": synthesis_res["assumptions"],
            "unknowns": synthesis_res["unknowns"],
            "related_knowledge": related_knowledge,
            "plan_trace": plan_trace,
            "latency_ms": total_ms
        }
