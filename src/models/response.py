"""
Response data models.
"""

from typing import List, Optional, Dict
from datetime import datetime

from pydantic import BaseModel, Field

from src.models.content import ContentItem
from src.models.analysis import Entity


class EvidenceBlock(BaseModel):
    """Evidence block with source references."""
    content_item: ContentItem = Field(..., description="Source content item")
    relevant_text: Optional[str] = Field(None, description="Relevant text excerpt")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in relevance")
    timestamp: datetime = Field(..., description="When evidence was found")


class SearchResult(BaseModel):
    """Individual search result."""
    entity: Entity = Field(..., description="Found entity")
    supporting_content: List[ContentItem] = Field(..., description="Supporting content items")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance to query")
    recency_score: float = Field(..., ge=0.0, le=1.0, description="Recency score")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    evidence_summary: str = Field(..., description="Summary of supporting evidence")


class RankedResult(BaseModel):
    """Ranked search result."""
    search_result: SearchResult = Field(..., description="Original search result")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final ranking score")
    rank_position: int = Field(..., ge=1, description="Position in ranking")


class Response(BaseModel):
    """Complete response to user query."""
    query: str = Field(..., description="Original user query")
    results: List[RankedResult] = Field(..., description="Ranked search results")
    total_found: int = Field(..., description="Total number of results found")
    response_text: str = Field(..., description="Natural language response")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall response confidence")
    processing_time: float = Field(..., description="Processing time in seconds")
    suggestions: List[str] = Field(default_factory=list, description="Alternative query suggestions")
    metadata: Dict = Field(default_factory=dict, description="Additional response metadata")