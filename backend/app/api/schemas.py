"""Pydantic schemas for TrustLens API"""
from typing import List, Optional
from pydantic import BaseModel, Field


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