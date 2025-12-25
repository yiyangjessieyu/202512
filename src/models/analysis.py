"""
Analysis data models.
"""

from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

from pydantic import BaseModel, Field


class EntityCategory(str, Enum):
    """Entity category enumeration."""
    PRODUCT = "product"
    LOCATION = "location"
    PERSON = "person"
    CONCEPT = "concept"
    BRAND = "brand"
    EVENT = "event"


class EntitySource(str, Enum):
    """Entity source enumeration."""
    CAPTION = "caption"
    HASHTAG = "hashtag"
    VISION = "vision"
    AUDIO = "audio"
    OCR = "ocr"


class Entity(BaseModel):
    """Extracted entity information."""
    name: str = Field(..., description="Entity name")
    category: EntityCategory = Field(..., description="Entity category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source: EntitySource = Field(..., description="Source of extraction")
    context: str = Field(..., description="Context where entity was found")


class VideoAnalysis(BaseModel):
    """Video analysis results."""
    content_id: str = Field(..., description="Associated content ID")
    frame_count: int = Field(..., description="Number of frames analyzed")
    detected_objects: List[str] = Field(default_factory=list, description="Objects detected in video")
    text_overlays: List[str] = Field(default_factory=list, description="Text overlays found")
    scene_descriptions: List[str] = Field(default_factory=list, description="Scene descriptions")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores")


class AudioTranscription(BaseModel):
    """Audio transcription results."""
    content_id: str = Field(..., description="Associated content ID")
    transcript: str = Field(..., description="Full transcript")
    segments: List[Dict] = Field(default_factory=list, description="Transcript segments with timestamps")
    language: Optional[str] = Field(None, description="Detected language")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")


class TextAnalysis(BaseModel):
    """Text analysis results."""
    content_id: str = Field(..., description="Associated content ID")
    extracted_entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    sentiment: Optional[str] = Field(None, description="Sentiment analysis")
    topics: List[str] = Field(default_factory=list, description="Identified topics")
    keywords: List[str] = Field(default_factory=list, description="Key terms")


class VisionAnalysis(BaseModel):
    """Vision analysis results."""
    content_id: str = Field(..., description="Associated content ID")
    detected_objects: List[str] = Field(default_factory=list, description="Detected objects")
    text_regions: List[str] = Field(default_factory=list, description="OCR text regions")
    scene_description: str = Field(..., description="Overall scene description")
    faces_detected: int = Field(default=0, description="Number of faces detected")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores")


class ContentAnalysis(BaseModel):
    """Complete content analysis results."""
    content_id: str = Field(..., description="Associated content ID")
    text_analysis: Optional[TextAnalysis] = Field(None, description="Text analysis results")
    vision_analysis: Optional[VisionAnalysis] = Field(None, description="Vision analysis results")
    audio_analysis: Optional[AudioTranscription] = Field(None, description="Audio analysis results")
    extracted_entities: List[Entity] = Field(default_factory=list, description="All extracted entities")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Overall confidence scores")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")