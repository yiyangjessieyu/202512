"""
Authentication data models.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class AuthStatus(str, Enum):
    """Authentication status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    INVALID = "invalid"


class UserCredentials(BaseModel):
    """User login credentials."""
    username: str = Field(..., description="Instagram username")
    password: str = Field(..., description="Instagram password")


class AuthResult(BaseModel):
    """Authentication result."""
    status: AuthStatus = Field(..., description="Authentication status")
    session_id: Optional[str] = Field(None, description="Session identifier")
    access_token: Optional[str] = Field(None, description="Access token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    message: Optional[str] = Field(None, description="Status message")


class SessionStatus(BaseModel):
    """Session status information."""
    session_id: str = Field(..., description="Session identifier")
    is_active: bool = Field(..., description="Whether session is active")
    expires_at: datetime = Field(..., description="Session expiration time")
    last_activity: datetime = Field(..., description="Last activity timestamp")