"""
Tests for AudioProcessor functionality.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import numpy as np

from src.analysis.audio_processor import AudioProcessor
from src.models.content import VideoFile, AudioFile
from src.models.analysis import AudioTranscription


class TestAudioProcessor:
    """Test cases for AudioProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = AudioProcessor()
    
    def create_test_audio_file(self, duration_seconds=2, sample_rate=16000):
        """Create a test audio file for testing."""
        # Create temporary audio file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Generate simple sine wave audio data
        samples = int(duration_seconds * sample_rate)
        frequency = 440  # A4 note
        t = np.linspace(0, duration_seconds, samples, False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Write WAV file (simple format)
        import wave
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_path
    
    def create_test_video_file(self):
        """Create a test video file for audio extraction testing."""
        # Create temporary video file (empty for testing)
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Write minimal MP4 header (for testing purposes)
        with open(temp_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp41')  # Minimal MP4 header
        
        return temp_path
    
    @patch('src.analysis.audio_processor.OpenAI')
    def test_transcribe_audio_success(self, mock_openai_class):
        """Test successful audio transcription."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = "Hello, this is a test transcription."
        mock_response.language = "en"
        mock_response.segments = [
            {
                'start': 0.0,
                'end': 2.0,
                'text': "Hello, this is a test transcription.",
                'avg_logprob': -0.5
            }
        ]
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Create test audio file
        audio_path = self.create_test_audio_file()
        
        try:
            audio_file = AudioFile(
                file_path=audio_path,
                duration=2.0,
                sample_rate=16000,
                channels=1
            )
            
            # Reinitialize processor to use mocked OpenAI
            processor = AudioProcessor()
            result = processor.transcribe_audio(audio_file)
            
            # Verify results
            assert isinstance(result, AudioTranscription)
            assert result.transcript == "Hello, this is a test transcription."
            assert result.language == "en"
            assert len(result.segments) == 1
            assert result.confidence > 0.0
            assert result.segments[0]['text'] == "Hello, this is a test transcription."
            
        finally:
            os.unlink(audio_path)
    
    def test_transcribe_audio_file_not_found(self):
        """Test transcription with non-existent file."""
        audio_file = AudioFile(
            file_path="/nonexistent/audio.wav",
            duration=2.0,
            sample_rate=16000,
            channels=1
        )
        
        with pytest.raises(FileNotFoundError):
            self.processor.transcribe_audio(audio_file)
    
    @patch('src.analysis.audio_processor.OpenAI')
    def test_transcribe_audio_api_error(self, mock_openai_class):
        """Test transcription with API error."""
        # Mock OpenAI to raise an exception
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        # Create test audio file
        audio_path = self.create_test_audio_file()
        
        try:
            audio_file = AudioFile(
                file_path=audio_path,
                duration=2.0,
                sample_rate=16000,
                channels=1
            )
            
            processor = AudioProcessor()
            result = processor.transcribe_audio(audio_file)
            
            # Should return error transcription
            assert isinstance(result, AudioTranscription)
            assert "failed" in result.transcript.lower()
            assert result.confidence == 0.0
            
        finally:
            os.unlink(audio_path)
    
    @patch('ffmpeg.run')
    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    def test_extract_audio_from_video_success(self, mock_input, mock_probe, mock_run):
        """Test successful audio extraction from video."""
        # Mock ffmpeg chain
        mock_stream = Mock()
        mock_output = Mock()
        mock_stream.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run = mock_run
        mock_input.return_value = mock_stream
        
        # Mock ffmpeg probe response
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'audio',
                'duration': '2.0',
                'sample_rate': '16000',
                'channels': '1'
            }]
        }
        
        # Mock ffmpeg run (extraction)
        mock_run.return_value = None
        
        # Create test video file
        video_path = self.create_test_video_file()
        
        try:
            video_file = VideoFile(
                file_path=video_path,
                duration=2.0,
                fps=30,
                resolution=(640, 480)
            )
            
            # Mock the creation of the output audio file
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = '/tmp/test_audio.wav'
                
                with patch('os.path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=1024):
                        result = self.processor.extract_audio_from_video(video_file)
                        
                        # Verify results
                        assert isinstance(result, AudioFile)
                        assert result.duration == 2.0
                        assert result.sample_rate == 16000
                        assert result.channels == 1
            
        finally:
            os.unlink(video_path)
    
    def test_extract_audio_from_video_file_not_found(self):
        """Test audio extraction with non-existent video file."""
        video_file = VideoFile(
            file_path="/nonexistent/video.mp4",
            duration=2.0,
            fps=30,
            resolution=(640, 480)
        )
        
        with pytest.raises(FileNotFoundError):
            self.processor.extract_audio_from_video(video_file)
    
    @patch('src.analysis.audio_processor.OpenAI')
    @patch('ffmpeg.run')
    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    def test_process_video_audio_integration(self, mock_input, mock_probe, mock_run, mock_openai_class):
        """Test complete video audio processing workflow."""
        # Mock ffmpeg chain
        mock_stream = Mock()
        mock_output = Mock()
        mock_stream.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_output
        mock_output.run = mock_run
        mock_input.return_value = mock_stream
        
        # Mock ffmpeg
        mock_probe.return_value = {
            'streams': [{
                'codec_type': 'audio',
                'duration': '2.0',
                'sample_rate': '16000',
                'channels': '1'
            }]
        }
        mock_run.return_value = None
        
        # Mock OpenAI
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.text = "Test video audio transcription."
        mock_response.language = "en"
        mock_response.segments = []
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Create test video file
        video_path = self.create_test_video_file()
        
        try:
            video_file = VideoFile(
                file_path=video_path,
                duration=2.0,
                fps=30,
                resolution=(640, 480)
            )
            
            # Mock file operations
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = '/tmp/test_audio.wav'
                
                with patch('os.path.exists', return_value=True):
                    with patch('os.path.getsize', return_value=1024):
                        with patch('builtins.open', mock_open(read_data=b'fake audio data')):
                            with patch('os.unlink'):  # Mock cleanup
                                processor = AudioProcessor()
                                result = processor.process_video_audio(video_file)
                                
                                # Verify results
                                assert isinstance(result, AudioTranscription)
                                assert result.transcript == "Test video audio transcription."
                                assert result.language == "en"
            
        finally:
            os.unlink(video_path)
    
    @patch('src.analysis.audio_processor.OpenAI')
    def test_process_audio_file_success(self, mock_openai_class):
        """Test processing standalone audio file."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = "Standalone audio file transcription."
        mock_response.language = "en"
        mock_response.segments = []
        mock_client.audio.transcriptions.create.return_value = mock_response
        
        # Create test audio file
        audio_path = self.create_test_audio_file()
        
        try:
            audio_file = AudioFile(
                file_path=audio_path,
                duration=2.0,
                sample_rate=16000,
                channels=1
            )
            
            processor = AudioProcessor()
            result = processor.process_audio_file(audio_file)
            
            # Verify results
            assert isinstance(result, AudioTranscription)
            assert result.transcript == "Standalone audio file transcription."
            assert result.language == "en"
            
        finally:
            os.unlink(audio_path)
    
    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        # Create test files
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_files.append(temp_file.name)
            temp_file.close()
        
        # Verify files exist
        for file_path in temp_files:
            assert os.path.exists(file_path)
        
        # Clean up
        self.processor.cleanup_temp_files(temp_files)
        
        # Verify files are deleted
        for file_path in temp_files:
            assert not os.path.exists(file_path)