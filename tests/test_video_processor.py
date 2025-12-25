"""
Tests for VideoProcessor functionality.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
import cv2
import numpy as np

from src.analysis.video_processor import VideoProcessor
from src.models.content import VideoFile, ImageFrame


class TestVideoProcessor:
    """Test cases for VideoProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = VideoProcessor()
    
    def create_test_video(self, duration_seconds=2, fps=30):
        """Create a test video file for testing."""
        # Create temporary video file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_path, fourcc, fps, (640, 480))
        
        # Write frames with different colors
        total_frames = duration_seconds * fps
        for i in range(total_frames):
            # Create frame with changing color
            color = (i * 255 // total_frames, 128, 255 - (i * 255 // total_frames))
            frame = np.full((480, 640, 3), color, dtype=np.uint8)
            
            # Add some text to make frames distinguishable
            cv2.putText(frame, f'Frame {i}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            writer.write(frame)
        
        writer.release()
        return temp_path
    
    def test_extract_frames_success(self):
        """Test successful frame extraction from video."""
        # Create test video
        video_path = self.create_test_video(duration_seconds=2, fps=30)
        
        try:
            video_file = VideoFile(
                file_path=video_path,
                duration=2.0,
                fps=30,
                resolution=(640, 480)
            )
            
            # Extract frames
            frames = self.processor.extract_frames(video_file, max_frames=5)
            
            # Verify results
            assert len(frames) <= 5
            assert len(frames) > 0
            
            for frame in frames:
                assert isinstance(frame, ImageFrame)
                assert os.path.exists(frame.file_path)
                assert frame.resolution == (640, 480)
                assert frame.timestamp is not None
                
                # Clean up frame file
                os.unlink(frame.file_path)
                
        finally:
            # Clean up test video
            if os.path.exists(video_path):
                os.unlink(video_path)
    
    def test_extract_frames_file_not_found(self):
        """Test frame extraction with non-existent file."""
        video_file = VideoFile(
            file_path="/nonexistent/video.mp4",
            duration=2.0,
            fps=30,
            resolution=(640, 480)
        )
        
        with pytest.raises(FileNotFoundError):
            self.processor.extract_frames(video_file)
    
    def test_extract_frames_invalid_video(self):
        """Test frame extraction with invalid video file."""
        # Create empty file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.write(b"invalid video data")
        temp_file.close()
        
        try:
            video_file = VideoFile(
                file_path=temp_path,
                duration=2.0,
                fps=30,
                resolution=(640, 480)
            )
            
            with pytest.raises(ValueError):
                self.processor.extract_frames(video_file)
                
        finally:
            os.unlink(temp_path)
    
    @patch('src.analysis.video_processor.OpenAI')
    def test_analyze_frame_with_gpt4v_success(self, mock_openai_class):
        """Test successful frame analysis with GPT-4V."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        Objects: person, car, building, tree
        Text overlays: "Welcome to the city"
        Scene: Urban street scene with pedestrians
        """
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create test image
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Create simple test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(temp_path, test_image)
        
        try:
            image_frame = ImageFrame(
                file_path=temp_path,
                timestamp=1.5,
                resolution=(100, 100)
            )
            
            # Reinitialize processor to use mocked OpenAI
            processor = VideoProcessor()
            result = processor.analyze_frame_with_gpt4v(image_frame)
            
            # Verify results
            assert isinstance(result, dict)
            assert "objects" in result
            assert "text_overlays" in result
            assert "scene_description" in result
            assert "confidence" in result
            assert "timestamp" in result
            assert result["timestamp"] == 1.5
            
        finally:
            os.unlink(temp_path)
    
    @patch('src.analysis.video_processor.OpenAI')
    def test_process_video_integration(self, mock_openai_class):
        """Test complete video processing workflow."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Objects: person, car\nText: Hello World"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create test video
        video_path = self.create_test_video(duration_seconds=1, fps=10)
        
        try:
            video_file = VideoFile(
                file_path=video_path,
                duration=1.0,
                fps=10,
                resolution=(640, 480)
            )
            
            # Process video
            processor = VideoProcessor()
            result = processor.process_video(video_file)
            
            # Verify results
            assert isinstance(result.frame_count, int)
            assert result.frame_count > 0
            assert isinstance(result.detected_objects, list)
            assert isinstance(result.text_overlays, list)
            assert isinstance(result.scene_descriptions, list)
            assert isinstance(result.confidence_scores, dict)
            assert "overall" in result.confidence_scores
            
        finally:
            if os.path.exists(video_path):
                os.unlink(video_path)
    
    def test_process_video_no_frames(self):
        """Test video processing when no frames can be extracted."""
        # Create empty video file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            video_file = VideoFile(
                file_path=temp_path,
                duration=0.0,
                fps=0,
                resolution=(0, 0)
            )
            
            # This should handle the error gracefully
            with pytest.raises(ValueError):
                self.processor.process_video(video_file)
                
        finally:
            os.unlink(temp_path)