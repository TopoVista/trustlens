"""Pydantic schemas for TrustLens API and Multi-Agent Extension"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# --- Legacy / Grounding Pipeline Schemas ---

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000, description="User query string")
    k: int = Field(5, ge=1, le=10, description="Number of documents to retrieve")


class HealthResponse(BaseModel):
    status: str
    version: str


class RetrievedDocument(BaseModel):
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document content")
    score: float = Field(..., description="Similarity score from FAISS")


class ClaimEvidence(BaseModel):
    id: str = Field(..., description="Evidence document ID")
    text: str = Field(..., description="Evidence document snippet")
    score: float = Field(..., description="Similarity score to claim")


class VerifiedClaim(BaseModel):
    claim: str
    label: str  # "SUPPORTED", "NOT_SUPPORTED", "CONTRADICTED"
    score: float
    color: str  # "green", "amber", "red"
    evidence: List[ClaimEvidence] = Field(default_factory=list)


class PipelineStats(BaseModel):
    claim_count: int = 0
    supported: int = 0
    not_supported: int = 0
    contradicted: int = 0
    faithfulness: float = 0.0
    hallucination_rate: float = 0.0
    retrieval_ms: float = 0.0
    generation_ms: float = 0.0
    verification_ms: float = 0.0
    total_ms: float = 0.0


class RAGResponse(BaseModel):
    query: str
    answer: str
    documents: List[RetrievedDocument]


class AnalyzeResponse(BaseModel):
    query: str
    answer: str
    documents: List[RetrievedDocument]
    verified_claims: List[VerifiedClaim]
    stats: PipelineStats


# --- Multi-Agent Vendor Risk Schemas ---

class VendorInput(BaseModel):
    id: Optional[str] = Field(None, description="Optional vendor ID for benchmark vendors (snowflake, datadog, stripe)")
    name: Optional[str] = Field("Custom Vendor", description="Vendor legal name")
    domain: Optional[str] = Field("vendor.internal", description="Vendor domain name")
    industry: Optional[str] = Field("Software & Technology", description="Industry classification")
    data_tier: Optional[str] = Field("Tier 2 (High)", description="Data classification tier")
    data_classified: Optional[List[str]] = Field(default_factory=list)
    self_attestations: Optional[Dict[str, str]] = Field(default_factory=dict)
    security_rating: Optional[int] = Field(85, ge=0, le=100)
    recent_breaches: Optional[int] = Field(0, ge=0)
    cve_critical_count: Optional[int] = Field(0, ge=0)


class VendorAssessmentRequest(BaseModel):
    vendor: VendorInput = Field(default_factory=VendorInput, description="Vendor profile or ID")
    query: Optional[str] = Field("", description="Specific audit focus or scope")
    documents_text: Optional[str] = Field("", description="Raw questionnaire text or policy excerpts")
    k: Optional[int] = Field(5, ge=1, le=10)


class ComplianceFinding(BaseModel):
    framework: str
    control_id: str
    title: str
    requirement: str
    status: str  # "Satisfied", "Partial", "Gap"
    confidence: float
    matched_evidence: str
    vendor_name: str


class RiskAssessmentResult(BaseModel):
    risk_score: float
    risk_tier: str  # "Low", "Moderate", "High", "Critical"
    inherent_risk: str
    residual_risk: str
    factors: Dict[str, Any]
    recommendation: str


class AgentExecutionTrace(BaseModel):
    agent: str
    role: str
    category: str
    status: str
    duration_ms: float
    error: Optional[str] = None


class QASeal(BaseModel):
    auditor: str
    model: str
    verified_claims_count: int
    certified: bool


class QAOverview(BaseModel):
    verified_claims: List[VerifiedClaim] = Field(default_factory=list)
    faithfulness: float = 100.0
    hallucination_rate: float = 0.0
    qa_status: str = "Passed"
    trust_seal: Optional[QASeal] = None


class VendorAssessmentResponse(BaseModel):
    vendor_profile: Dict[str, Any]
    parsed_controls: List[Dict[str, Any]]
    compliance_findings: List[ComplianceFinding]
    compliance_rate: float
    risk_assessment: RiskAssessmentResult
    report_narrative: str
    qa_verification: QAOverview
    evidence_documents: List[Dict[str, Any]]
    agent_traces: List[AgentExecutionTrace]
    total_latency_ms: float


class QARequest(BaseModel):
    vendor: VendorInput = Field(default_factory=VendorInput)
    question: str = Field(..., min_length=1, max_length=2000, description="Analyst query about vendor")


class QAResponse(BaseModel):
    question: str
    answer: str
    citations: List[str]
    vendor_name: str


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
    chunks_count: int
    claims_extracted: int
    entities_extracted: int
    events_extracted: int
    is_tabular: bool
    dataset_profile: Optional[Dict[str, Any]] = None


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