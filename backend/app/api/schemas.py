"""Pydantic schemas for the TrustLens workspace API."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


# --- Personal Knowledge Intelligence Schemas ---

class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field("", max_length=500)


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    filename: Optional[str] = "document.txt"
    file_type: Optional[str] = "text"  # text, markdown, csv
    raw_content: str = Field(..., min_length=1)
    authority_level: Optional[str] = "MEDIUM"  # HIGH, MEDIUM, LOW


class DocumentResponse(BaseModel):
    document_id: str
    title: str
    authority_level: str
    chunks_count: int
    claims_extracted: int
    entities_extracted: int
    events_extracted: int
    is_tabular: bool
    dataset_profile: Optional[Dict[str, Any]] = None
    relationships_extracted: int = 0
    graph_nodes_created: int = 0
    graph_edges_created: int = 0
    ingestion_status: str = "READY"
    deduplicated: bool = False


class SemanticRuleRequest(BaseModel):
    rule_type: str = Field(..., description="term_definition, entity_alias, authority_override, constraint")
    rule_key: str = Field(...)
    rule_value: str = Field(...)


class SemanticRuleResponse(BaseModel):
    id: str
    workspace_id: str
    rule_type: str
    rule_key: str
    rule_value: str
    created_at: str


class KnowledgeHealthResponse(BaseModel):
    documents: int
    claims: int
    entities: int
    events: int
    evidence_links: int
    graph_nodes: int = 0
    graph_edges: int = 0
    breakdown: Dict[str, Any]
    major_contradictions: int
    knowledge_gaps: int


class ProactiveDiscoveryItem(BaseModel):
    type: str
    title: str
    severity: str
    summary: str
    evidence: str
    source: str
    detail: str


class ProactiveDiscoveryResponse(BaseModel):
    discoveries: List[ProactiveDiscoveryItem]


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=3000)


class KnowledgeEvidenceItem(BaseModel):
    source: str
    filename: str
    passage: str
    location: str
    score: float


class KnowledgeQueryResponse(BaseModel):
    query: str
    intent: str
    answer: str
    confidence: float
    claims: List[Dict[str, Any]]
    evidence: List[KnowledgeEvidenceItem]
    contradictions: List[Dict[str, Any]]
    assumptions: List[str]
    unknowns: List[str]
    related_knowledge: Dict[str, Any]
    plan_trace: List[str]
    latency_ms: float


class GraphNodeResponse(BaseModel):
    id: str
    type: str
    label: str
    reference_type: str
    reference_id: str
    status: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    confidence: float
    explanation: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceGraphResponse(BaseModel):
    nodes: List[GraphNodeResponse] = Field(default_factory=list)
    edges: List[GraphEdgeResponse] = Field(default_factory=list)
    stats: Dict[str, int] = Field(default_factory=dict)
