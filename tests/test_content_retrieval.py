"""
Tests for content retrieval engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.content.retrieval import ContentRetrievalEngine
from src.models.content import ContentItem, ContentType, MediaType, EngagementData


class TestContentRetrievalEngine:
    """Test cases for ContentRetrievalEngine."""
    
    def test_init(self):
        """Test engine initialization."""
        engine = ContentRetrievalEngine(headless=True, download_dir="test_temp")
        
        assert engine.headless is True
        assert engine.download_dir == "test_temp"
        assert engine.driver is None
        assert engine.wait is None
        assert engine.rate_limit_delay == 1.0
        assert engine.max_retries == 3
    
    def test_extract_content_id(self):
        """Test content ID extraction from URLs."""
        engine = ContentRetrievalEngine()
        
        # Test post URL
        post_url = "https://www.instagram.com/p/ABC123DEF/"
        assert engine._extract_content_id(post_url) == "ABC123DEF"
        
        # Test reel URL
        reel_url = "https://www.instagram.com/reel/XYZ789GHI/"
        assert engine._extract_content_id(reel_url) == "XYZ789GHI"
        
        # Test invalid URL
        invalid_url = "https://www.instagram.com/user/profile/"
        assert engine._extract_content_id(invalid_url) is None
    
    @patch('src.content.retrieval.webdriver.Chrome')
    def test_setup_driver(self, mock_chrome):
        """Test WebDriver setup."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        engine = ContentRetrievalEngine(headless=True)
        driver = engine._setup_driver()
        
        # Verify Chrome was called
        mock_chrome.assert_called_once()
        
        # Verify execute_script was called to hide webdriver property
        mock_driver.execute_script.assert_called_with(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    
    def test_human_like_delay(self):
        """Test human-like delay functionality."""
        engine = ContentRetrievalEngine()
        
        # Test that delay is called (we can't easily test the actual sleep)
        with patch('time.sleep') as mock_sleep:
            engine._human_like_delay(1.0, 2.0)
            mock_sleep.assert_called_once()
            
            # Verify delay is within expected range
            call_args = mock_sleep.call_args[0][0]
            assert 1.0 <= call_args <= 2.0
    
    def test_handle_rate_limits(self):
        """Test rate limiting logic."""
        engine = ContentRetrievalEngine()
        initial_delay = engine.rate_limit_delay
        
        with patch('time.sleep') as mock_sleep:
            engine.handle_rate_limits()
            
            # Verify delay was doubled
            assert engine.rate_limit_delay == initial_delay * 2
            
            # Verify sleep was called with new delay
            mock_sleep.assert_called_once_with(engine.rate_limit_delay)
    
    def test_rate_limit_cap(self):
        """Test that rate limit delay is capped at 60 seconds."""
        engine = ContentRetrievalEngine()
        engine.rate_limit_delay = 50.0  # Set high initial value
        
        with patch('time.sleep'):
            engine.handle_rate_limits()
            
            # Should be capped at 60 seconds
            assert engine.rate_limit_delay == 60.0
    
    @patch('requests.get')
    @patch('os.path.getsize')
    @patch('builtins.open', create=True)
    def test_download_file(self, mock_open, mock_getsize, mock_requests):
        """Test file download functionality."""
        # Setup mocks
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'test_data']
        mock_requests.return_value = mock_response
        mock_getsize.return_value = 1024
        
        engine = ContentRetrievalEngine(download_dir="test_temp")
        
        # Test download
        media_file = engine._download_file("http://example.com/video.mp4", MediaType.VIDEO)
        
        # Verify file properties
        assert media_file.media_type == MediaType.VIDEO
        assert media_file.file_size == 1024
        assert "test_temp" in media_file.file_path
        assert media_file.file_path.endswith(".mp4")
        
        # Verify requests was called
        mock_requests.assert_called_once_with("http://example.com/video.mp4", stream=True)


if __name__ == "__main__":
    pytest.main([__file__])