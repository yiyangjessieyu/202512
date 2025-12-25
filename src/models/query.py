"""
Query data models.
"""

from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Query intent type enumeration."""
    SEARCH = "search"
    RANKING = "ranking"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"


class ContentCategory(str, Enum):
    """Content category enumeration."""
    PRODUCTS = "products"
    LOCATIONS = "locations"
    ADVICE = "advice"
    TUTORIALS = "tutorials"
    RECIPES = "recipes"
    FASHION = "fashion"
    TRAVEL = "travel"
    FITNESS = "fitness"
    GENERAL = "general"


class QueryConstraints(BaseModel):
    """Query constraints and filters."""
    max_results: Optional[int] = Field(None, description="Maximum number of results")
    location_filter: Optional[str] = Field(None, description="Geographic location filter")
    date_range: Optional[tuple] = Field(None, description="Date range filter")
    category_filter: Optional[ContentCategory] = Field(None, description="Category filter")
    confidence_threshold: float = Field(default=0.5, description="Minimum confidence threshold")


class QueryIntent(BaseModel):
    """Parsed query intent."""
    original_query: str = Field(..., description="Original user query")
    intent_type: IntentType = Field(..., description="Type of intent")
    target_category: ContentCategory = Field(..., description="Target content category")
    constraints: QueryConstraints = Field(default_factory=QueryConstraints, description="Query constraints")
    expected_count: Optional[int] = Field(None, description="Expected number of results")
    entities: List[str] = Field(default_factory=list, description="Extracted entities from query")
    keywords: List[str] = Field(default_factory=list, description="Key terms from query")