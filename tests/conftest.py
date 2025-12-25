"""
Pytest configuration and fixtures.
"""

import pytest
from starlette.testclient import TestClient

from src.main import app
from src.config.settings import get_settings


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def settings():
    """Settings fixture."""
    return get_settings()


@pytest.fixture
def sample_credentials():
    """Sample user credentials for testing."""
    return {
        "username": "test_user",
        "password": "test_password"
    }


@pytest.fixture
def sample_content_item():
    """Sample content item for testing."""
    return {
        "id": "test_content_123",
        "url": "https://instagram.com/p/test123",
        "content_type": "post",
        "timestamp": "2023-01-01T00:00:00Z",
        "author": "test_author",
        "caption": "Test caption #test",
        "hashtags": ["test"],
        "media_files": [],
        "engagement_metrics": {
            "likes": 100,
            "comments": 10,
            "shares": 5
        }
    }