"""Entity Specialist for TrustLens Knowledge Graph"""
import re
from typing import Any, Dict, List
from app.specialists.base import BaseSpecialist


class EntityAgent(BaseSpecialist):
    """
    Extracts, resolves, and deduplicates entities across workspace documents.
    Maps aliases and links entities to canonical knowledge graph representations.
    """

    def __init__(self):
        super().__init__(
            name="Entity Specialist",
            description="Extracts named entities, resolves aliases, and identifies graph connections",
            capabilities=["entity_extraction", "entity_resolution", "alias_mapping"]
        )

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        text = context.get("text", "")
        semantic_rules = context.get("semantic_rules", [])

        if not text.strip():
            return {"entities": [], "relationships": []}

        # Rule-based and pattern entity detection
        extracted_entities = []

        # 1. Organizations & Companies
        org_pattern = r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*(?:\s+(?:Inc\.|Corp\.|LLC|Ltd\.|Technologies|Cloud|Systems|AI|Labs))?)\b"
        matches = re.findall(org_pattern, text)
        for m in matches:
            cleaned = m.strip()
            if len(cleaned) > 2 and cleaned not in {"The", "This", "These", "However", "When", "Table", "Figure", "Document"}:
                extracted_entities.append({
                    "name": cleaned,
                    "entity_type": "Organization",
                    "aliases": [cleaned.lower(), cleaned.replace(".", "")]
                })

        # 2. Metrics & Technical Concepts
        metric_pattern = r"\b((?:Revenue|ARR|MRR|Churn|EBITDA|Latency|Throughput|SLA|ACID|MVCC|B-tree|GDPR|SOC\s*2|ISO\s*27001))\b"
        concept_matches = re.findall(metric_pattern, text, re.IGNORECASE)
        for c in concept_matches:
            extracted_entities.append({
                "name": c.strip().title(),
                "entity_type": "Metric" if c.upper() in {"REVENUE", "ARR", "MRR", "CHURN", "EBITDA"} else "Concept",
                "aliases": [c.lower()]
            })

        # 3. Apply User-Defined Semantic Rules (Alias / Terminology)
        canonical_map = {}
        for rule in semantic_rules:
            if rule.get("rule_type") in {"entity_alias", "term_definition"}:
                canonical_map[rule.get("rule_key", "").lower()] = rule.get("rule_value")

        # Deduplicate and apply canonical rules
        deduped = {}
        for ent in extracted_entities:
            key = ent["name"].lower()
            canonical_name = canonical_map.get(key, ent["name"])
            if canonical_name not in deduped:
                deduped[canonical_name] = {
                    "name": canonical_name,
                    "entity_type": ent["entity_type"],
                    "aliases": list(set(ent["aliases"] + [ent["name"].lower()]))
                }

        entities_list = list(deduped.values())

        # 4. Extract Relationships between co-occurring entities
        relationships = []
        if len(entities_list) >= 2:
            for i in range(len(entities_list) - 1):
                e1 = entities_list[i]
                e2 = entities_list[i + 1]
                relationships.append({
                    "source": e1["name"],
                    "target": e2["name"],
                    "relation_type": "related_to",
                    "evidence": f"Co-occurs in workspace document context."
                })

        return {"entities": entities_list, "relationships": relationships}
