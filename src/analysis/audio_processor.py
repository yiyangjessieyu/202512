"""
Audio processing module for transcription and audio analysis.
"""

import os
import logging
import tempfile
from typing import List, Dict, Optional
from pathlib import Path
import ffmpeg

from openai import OpenAI

from src.models.analysis import AudioTranscription
from src.models.content import VideoFile, AudioFile
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Processes audio files for transcription using OpenAI Whisper.
    
    Extracts audio from video files using ffmpeg and transcribes speech content.
    Implements requirement 3.2: Transcribe speech and identify background music.
    """
    
    def __init__(self):
        """Initialize the audio processor with OpenAI client."""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.mov', '.avi']
        self.max_file_size_mb = 25  # OpenAI Whisper API limit
        
    def extract_audio_from_video(self, video_file: VideoFile) -> AudioFile:
        """
        Extract audio track from video file using ffmpeg.
        
        Args:
            video_file: Video file to extract audio from
            
        Returns:
            AudioFile object with extracted audio
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If audio extraction fails
        """
        if not os.path.exists(video_file.file_path):
            raise FileNotFoundError(f"Video file not found: {video_file.file_path}")
            
        logger.info(f"Extracting audio from video: {video_file.file_path}")
        
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_audio_path = temp_file.name
            
            # Use ffmpeg to extract audio
            (
                ffmpeg
                .input(video_file.file_path)
                .output(
                    temp_audio_path,
                    acodec='pcm_s16le',  # WAV format
                    ac=1,  # Mono channel
                    ar=16000  # 16kHz sample rate (optimal for Whisper)
                )
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )
            
            # Verify the audio file was created
            if not os.path.exists(temp_audio_path):
                raise ValueError("Audio extraction failed - no output file created")
                
            # Get audio file properties
            probe = ffmpeg.probe(temp_audio_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            if not audio_stream:
                raise ValueError("No audio stream found in extracted file")
                
            duration = float(audio_stream.get('duration', 0))
            sample_rate = int(audio_stream.get('sample_rate', 16000))
            channels = int(audio_stream.get('channels', 1))
            
            # Check file size
            file_size = os.path.getsize(temp_audio_path)
            if file_size > self.max_file_size_mb * 1024 * 1024:
                logger.warning(f"Audio file size ({file_size / 1024 / 1024:.1f}MB) exceeds Whisper limit")
                # Could implement chunking here if needed
                
            audio_file = AudioFile(
                file_path=temp_audio_path,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels
            )
            
            logger.info(f"Audio extracted successfully: {duration:.2f}s, {sample_rate}Hz, {channels} channels")
            return audio_file
            
        except ffmpeg.Error as e:
            error_msg = f"FFmpeg error during audio extraction: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {str(e)}")
            raise ValueError(f"Audio extraction failed: {str(e)}")
    
    def transcribe_audio(self, audio_file: AudioFile) -> AudioTranscription:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        Args:
            audio_file: Audio file to transcribe
            
        Returns:
            AudioTranscription with transcript and metadata
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If transcription fails
        """
        if not os.path.exists(audio_file.file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file.file_path}")
            
        logger.info(f"Transcribing audio file: {audio_file.file_path}")
        
        try:
            # Check file size
            file_size = os.path.getsize(audio_file.file_path)
            if file_size > self.max_file_size_mb * 1024 * 1024:
                raise ValueError(f"Audio file too large ({file_size / 1024 / 1024:.1f}MB). Maximum size is {self.max_file_size_mb}MB")
            
            # Open audio file and send to Whisper API
            with open(audio_file.file_path, "rb") as audio_data:
                response = self.client.audio.transcriptions.create(
                    model=self.settings.openai_audio_model,
                    file=audio_data,
                    response_format="verbose_json",  # Get detailed response with timestamps
                    language=None  # Auto-detect language
                )
            
            # Extract transcription data
            transcript = response.text
            language = getattr(response, 'language', None)
            
            # Process segments if available
            segments = []
            if hasattr(response, 'segments') and response.segments:
                for segment in response.segments:
                    segments.append({
                        'start': segment.get('start', 0),
                        'end': segment.get('end', 0),
                        'text': segment.get('text', ''),
                        'confidence': segment.get('avg_logprob', 0.0)  # Whisper uses log probabilities
                    })
            
            # Calculate overall confidence (Whisper doesn't provide this directly)
            # We'll use a heuristic based on transcript length and segment confidence
            if segments:
                avg_confidence = sum(seg.get('confidence', 0) for seg in segments) / len(segments)
                # Convert log probability to confidence score (rough approximation)
                confidence = max(0.0, min(1.0, (avg_confidence + 5) / 5))  # Normalize from [-5, 0] to [0, 1]
            else:
                # If no segments, estimate confidence based on transcript quality
                confidence = 0.8 if len(transcript.strip()) > 10 else 0.5
            
            logger.info(f"Transcription completed: {len(transcript)} characters, "
                       f"language: {language}, confidence: {confidence:.2f}")
            
            return AudioTranscription(
                content_id="",  # Will be set by caller
                transcript=transcript,
                segments=segments,
                language=language,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Transcription failed for {audio_file.file_path}: {str(e)}")
            # Return empty transcription with error info
            return AudioTranscription(
                content_id="",
                transcript=f"Transcription failed: {str(e)}",
                segments=[],
                language=None,
                confidence=0.0
            )
    
    def process_video_audio(self, video_file: VideoFile) -> AudioTranscription:
        """
        Extract audio from video and transcribe it.
        
        Args:
            video_file: Video file to process
            
        Returns:
            AudioTranscription results
        """
        logger.info(f"Processing audio from video: {video_file.file_path}")
        
        audio_file = None
        try:
            # Extract audio from video
            audio_file = self.extract_audio_from_video(video_file)
            
            # Transcribe the extracted audio
            transcription = self.transcribe_audio(audio_file)
            
            logger.info(f"Video audio processing completed for {video_file.file_path}")
            return transcription
            
        except Exception as e:
            logger.error(f"Video audio processing failed: {str(e)}")
            return AudioTranscription(
                content_id="",
                transcript=f"Audio processing failed: {str(e)}",
                segments=[],
                language=None,
                confidence=0.0
            )
        finally:
            # Clean up temporary audio file
            if audio_file and os.path.exists(audio_file.file_path):
                try:
                    os.unlink(audio_file.file_path)
                    logger.debug(f"Cleaned up temporary audio file: {audio_file.file_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete temporary audio file: {str(e)}")
    
    def process_audio_file(self, audio_file: AudioFile) -> AudioTranscription:
        """
        Process standalone audio file for transcription.
        
        Args:
            audio_file: Audio file to process
            
        Returns:
            AudioTranscription results
        """
        logger.info(f"Processing audio file: {audio_file.file_path}")
        
        try:
            # Check if file format is supported
            file_ext = Path(audio_file.file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"Unsupported audio format: {file_ext}")
                # Try to convert using ffmpeg
                audio_file = self._convert_audio_format(audio_file)
            
            # Transcribe the audio
            transcription = self.transcribe_audio(audio_file)
            
            logger.info(f"Audio file processing completed for {audio_file.file_path}")
            return transcription
            
        except Exception as e:
            logger.error(f"Audio file processing failed: {str(e)}")
            return AudioTranscription(
                content_id="",
                transcript=f"Audio processing failed: {str(e)}",
                segments=[],
                language=None,
                confidence=0.0
            )
    
    def _convert_audio_format(self, audio_file: AudioFile) -> AudioFile:
        """
        Convert audio file to supported format using ffmpeg.
        
        Args:
            audio_file: Audio file to convert
            
        Returns:
            AudioFile with converted format
        """
        logger.info(f"Converting audio format for: {audio_file.file_path}")
        
        try:
            # Create temporary converted file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_audio_path = temp_file.name
            
            # Convert using ffmpeg
            (
                ffmpeg
                .input(audio_file.file_path)
                .output(
                    temp_audio_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar=16000
                )
                .overwrite_output()
                .run(quiet=True, capture_stdout=True, capture_stderr=True)
            )
            
            # Get properties of converted file
            probe = ffmpeg.probe(temp_audio_path)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            duration = float(audio_stream.get('duration', audio_file.duration))
            sample_rate = int(audio_stream.get('sample_rate', 16000))
            channels = int(audio_stream.get('channels', 1))
            
            return AudioFile(
                file_path=temp_audio_path,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels
            )
            
        except Exception as e:
            logger.error(f"Audio format conversion failed: {str(e)}")
            raise ValueError(f"Audio conversion failed: {str(e)}")
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        Clean up temporary audio files.
        
        Args:
            file_paths: List of file paths to clean up
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up temporary file: {file_path}")
            except OSError as e:
                logger.warning(f"Failed to delete temporary file {file_path}: {str(e)}")