"""
Multi-Modal Analysis Pipeline for processing different content types.
"""

from typing import List
from dataclasses import dataclass

from src.models.analysis import VideoAnalysis, AudioTranscription, TextAnalysis, VisionAnalysis
from src.models.content import VideoFile, AudioFile, ImageFrame
from src.analysis.video_processor import VideoProcessor
from src.analysis.audio_processor import AudioProcessor
from src.analysis.text_processor import TextProcessor


@dataclass
class MultiModalAnalyzer:
    """Processes different content types to extract structured information."""
    
    def __init__(self):
        """Initialize the multi-modal analyzer."""
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor()
    
    def process_video(self, video_file: VideoFile) -> VideoAnalysis:
        """
        Extracts frames and analyzes visual content.
        
        Args:
            video_file: Video file to process
            
        Returns:
            Video analysis results
        """
        return self.video_processor.process_video(video_file)
    
    def process_audio(self, audio_file: AudioFile) -> AudioTranscription:
        """
        Transcribes speech and identifies audio elements.
        
        Args:
            audio_file: Audio file to process
            
        Returns:
            Audio transcription results
        """
        return self.audio_processor.process_audio_file(audio_file)
    
    def process_video_audio(self, video_file: VideoFile) -> AudioTranscription:
        """
        Extracts audio from video and transcribes it.
        
        Args:
            video_file: Video file to process
            
        Returns:
            Audio transcription results
        """
        return self.audio_processor.process_video_audio(video_file)
    
    def process_text(self, text_content: str) -> TextAnalysis:
        """
        Analyzes captions, hashtags, and comments.
        
        Args:
            text_content: Text content to analyze
            
        Returns:
            Text analysis results
        """
        return self.text_processor.process_text_content(text_content)
    
    def process_images(self, image_frames: List[ImageFrame]) -> VisionAnalysis:
        """
        Identifies objects, text overlays, and visual elements.
        
        Args:
            image_frames: List of image frames to analyze
            
        Returns:
            Vision analysis results
        """
        # TODO: Implement image analysis with GPT-4V
        pass