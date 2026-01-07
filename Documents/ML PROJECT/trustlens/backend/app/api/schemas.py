"""Pydantic schemas"""
from typing import List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="User query string")
    k: int = Field(5, description="Number of documents to retrieve")


class RetrievedDocument(BaseModel):
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document content")
    score: float = Field(..., description="Similarity score from FAISS")


class RAGResponse(BaseModel):
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer")
    documents: List[RetrievedDocument] = Field(
        ..., description="Documents used to generate the answer"
    )

class VerifiedClaim(BaseModel):
    claim: str
    label: str
    score: float
    color: str


class AnalyzeResponse(BaseModel):
    query: str
    answer: str
    verified_claims: List[VerifiedClaim]