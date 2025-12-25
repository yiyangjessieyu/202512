"""
Content data models.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Content type enumeration."""
    POST = "post"
    REEL = "reel"
    CAROUSEL = "carousel"


class MediaType(str, Enum):
    """Media type enumeration."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class MediaFile(BaseModel):
    """Media file information."""
    file_path: str = Field(..., description="Path to media file")
    media_type: MediaType = Field(..., description="Type of media")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    resolution: Optional[Tuple[int, int]] = Field(None, description="Resolution (width, height)")
    file_size: int = Field(..., description="File size in bytes")


class EngagementData(BaseModel):
    """Engagement metrics for content."""
    likes: int = Field(default=0, description="Number of likes")
    comments: int = Field(default=0, description="Number of comments")
    shares: int = Field(default=0, description="Number of shares")
    views: Optional[int] = Field(None, description="Number of views (for videos)")


class ContentItem(BaseModel):
    """Instagram content item."""
    id: str = Field(..., description="Unique content identifier")
    url: str = Field(..., description="Instagram URL")
    content_type: ContentType = Field(..., description="Type of content")
    timestamp: datetime = Field(..., description="Content creation timestamp")
    author: str = Field(..., description="Content author username")
    caption: str = Field(default="", description="Content caption")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used")
    media_files: List[MediaFile] = Field(default_factory=list, description="Associated media files")
    engagement_metrics: EngagementData = Field(default_factory=EngagementData, description="Engagement data")


class ContentMetadata(BaseModel):
    """Content metadata extracted during processing."""
    content_id: str = Field(..., description="Associated content ID")
    extracted_text: List[str] = Field(default_factory=list, description="Extracted text from media")
    detected_objects: List[str] = Field(default_factory=list, description="Detected objects in images/video")
    audio_features: Optional[dict] = Field(None, description="Audio analysis features")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing timestamp")


class VideoFile(BaseModel):
    """Video file for processing."""
    file_path: str = Field(..., description="Path to video file")
    duration: float = Field(..., description="Video duration in seconds")
    fps: int = Field(..., description="Frames per second")
    resolution: Tuple[int, int] = Field(..., description="Video resolution")


class AudioFile(BaseModel):
    """Audio file for processing."""
    file_path: str = Field(..., description="Path to audio file")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Audio sample rate")
    channels: int = Field(..., description="Number of audio channels")


class ImageFrame(BaseModel):
    """Image frame for analysis."""
    file_path: str = Field(..., description="Path to image file")
    timestamp: Optional[float] = Field(None, description="Timestamp in video (if from video)")
    resolution: Tuple[int, int] = Field(..., description="Image resolution")