"""
Tests for main application.
"""

import pytest
import asyncio
from src.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint returns correct response."""
    # Test the root function directly
    from src.main import root
    result = await root()
    
    assert result["message"] == "Instagram Content Analyzer API"
    assert result["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    # Test the health check function directly
    from src.main import health_check
    result = await health_check()
    
    assert result["status"] == "healthy"
    assert result["service"] == "instagram-content-analyzer"


def test_app_creation():
    """Test that the FastAPI app is created successfully."""
    assert app is not None
    assert app.title == "Instagram Content Analyzer"
    assert app.version == "0.1.0"