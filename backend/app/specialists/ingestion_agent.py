"""Ingestion and Knowledge Extraction Specialist for TrustLens"""
import re
from typing import Any, Dict, List, Optional
from app.specialists.base import BaseSpecialist
from app.specialists.claim_detective import ClaimDetective
from app.specialists.entity_agent import EntityAgent
from app.specialists.timeline_agent import TimelineAgent
from app.specialists.data_analyst import DataAnalyst
from app.knowledge.repository import KnowledgeRepository


class IngestionKnowledgeAgent(BaseSpecialist):
    """
    Transforms raw uploaded files and notes into structured intelligence:
    - Identifies document structure & chunks with precise coordinates
    - Extracts entities and updates Knowledge Graph
    - Extracts claims and updates Claim Graph
    - Detects dates and updates Chronological Timeline
    - Profiles structured datasets if CSV/table
    """

    def __init__(self, repo: Optional[KnowledgeRepository] = None):
        super().__init__(
            name="Ingestion Specialist",
            description="Ingests documents and structured files, performing chunking and graph extraction",
            capabilities=["document_ingestion", "structural_chunking", "graph_population"]
        )
        self.repo = repo or KnowledgeRepository()
        self.claim_detective = ClaimDetective()
        self.entity_agent = EntityAgent()
        self.timeline_agent = TimelineAgent()
        self.data_analyst = DataAnalyst()

    async def ingest_content(
        self,
        workspace_id: str,
        title: str,
        filename: str,
        raw_content: str,
        file_type: str = "text",
        authority_level: str = "MEDIUM"
    ) -> Dict[str, Any]:
        """
        Complete ingestion pipeline: stores doc, creates chunks, extracts entities,
        claims, timeline events, and dataset profiles.
        """
        # 1. Store document in repository
        doc_id = self.repo.add_document(
            workspace_id=workspace_id,
            title=title,
            filename=filename,
            file_type=file_type,
            raw_content=raw_content,
            authority_level=authority_level
        )

        # 2. Check if tabular data (CSV / TSV)
        is_tabular = file_type.lower() in {"csv", "tsv"} or ("," in raw_content and "\n" in raw_content and len(raw_content.splitlines()) > 2)
        dataset_profile = None

        if is_tabular:
            profile_res = await self.data_analyst.analyze(workspace_id, {"raw_content": raw_content, "filename": filename})
            if profile_res.get("is_tabular"):
                self.repo.add_dataset_profile(
                    workspace_id=workspace_id,
                    document_id=doc_id,
                    row_count=profile_res["row_count"],
                    col_count=profile_res["col_count"],
                    columns=profile_res["headers"],
                    profile=profile_res["columns_profile"],
                    insights=profile_res["insights"]
                )
                dataset_profile = profile_res

        # 3. Structural Chunking with location references
        chunks_data = self._chunk_document(workspace_id, doc_id, raw_content, is_tabular)
        self.repo.add_chunks(chunks_data)

        # 4. Extract Entities
        semantic_rules = self.repo.get_semantic_rules(workspace_id)
        ent_res = await self.entity_agent.analyze(workspace_id, {"text": raw_content, "semantic_rules": semantic_rules})
        for ent in ent_res.get("entities", []):
            self.repo.add_entity(workspace_id, ent["name"], ent["entity_type"], ent.get("aliases"))

        # 5. Extract Claims
        claim_res = await self.claim_detective.analyze(workspace_id, {"text": raw_content, "document_id": doc_id})
        for c in claim_res.get("claims", []):
            claim_id = self.repo.add_claim(
                workspace_id=workspace_id,
                statement=c["statement"],
                document_id=doc_id,
                claim_type=c["claim_type"],
                confidence=c["confidence"]
            )
            # Link to first matching chunk as immediate evidence
            if chunks_data:
                matching_chunk = next((chk for chk in chunks_data if c["statement"][:30] in chk["text"]), chunks_data[0])
                self.repo.add_evidence(
                    workspace_id=workspace_id,
                    claim_id=claim_id,
                    document_id=doc_id,
                    chunk_id=matching_chunk.get("id"),
                    exact_passage=matching_chunk["text"][:250],
                    location_ref=matching_chunk.get("location_info", "Section 1"),
                    strength=0.85
                )

        # 6. Extract Timeline Events
        time_res = await self.timeline_agent.analyze(workspace_id, {"text": raw_content, "document_id": doc_id})
        for evt in time_res.get("events", []):
            self.repo.add_event(
                workspace_id=workspace_id,
                title=evt["title"],
                date_str=evt["date_str"],
                description=evt["description"],
                document_id=doc_id,
                timestamp_val=evt["timestamp_val"]
            )

        return {
            "document_id": doc_id,
            "title": title,
            "chunks_count": len(chunks_data),
            "claims_extracted": len(claim_res.get("claims", [])),
            "entities_extracted": len(ent_res.get("entities", [])),
            "events_extracted": len(time_res.get("events", [])),
            "is_tabular": is_tabular,
            "dataset_profile": dataset_profile
        }

    def _chunk_document(self, workspace_id: str, doc_id: str, content: str, is_tabular: bool) -> List[Dict[str, Any]]:
        """Splits content into coherent structural chunks with location coordinates."""
        chunks = []
        if is_tabular:
            # Chunk table in batches of rows
            lines = content.strip().splitlines()
            header = lines[0] if lines else ""
            batch_size = 15
            for i in range(1, len(lines), batch_size):
                batch = lines[i:i + batch_size]
                text = header + "\n" + "\n".join(batch)
                chunks.append({
                    "workspace_id": workspace_id,
                    "document_id": doc_id,
                    "chunk_index": len(chunks),
                    "text": text,
                    "location_info": f"Rows {i} to {min(i + batch_size - 1, len(lines) - 1)}"
                })
        else:
            # Chunk text by paragraphs / sections
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if len(p.strip()) > 30]
            if not paragraphs:
                paragraphs = [content.strip()]

            for idx, p in enumerate(paragraphs):
                chunks.append({
                    "workspace_id": workspace_id,
                    "document_id": doc_id,
                    "chunk_index": idx,
                    "text": p,
                    "location_info": f"Section {idx + 1}, Paragraph 1"
                })

        return chunks

    async def analyze(self, workspace_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return await self.ingest_content(
            workspace_id=workspace_id,
            title=context.get("title", "Untitled Document"),
            filename=context.get("filename", "document.txt"),
            raw_content=context.get("raw_content", ""),
            file_type=context.get("file_type", "text"),
            authority_level=context.get("authority_level", "MEDIUM")
        )
