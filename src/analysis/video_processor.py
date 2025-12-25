"""
Video processing module for frame extraction and visual analysis.
"""

import os
import cv2
import base64
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import tempfile

from openai import OpenAI

from src.models.analysis import VideoAnalysis
from src.models.content import VideoFile, ImageFrame
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Processes video files to extract frames and perform visual analysis.
    
    Uses OpenCV for frame extraction and GPT-4V for visual content analysis.
    Implements requirement 3.1: Extract text overlays and visual elements using computer vision.
    """
    
    def __init__(self):
        """Initialize the video processor with OpenAI client."""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.max_frames = 10  # Limit frames for API efficiency
        self.frame_interval = 1.0  # Extract frame every second
        
    def extract_frames(self, video_file: VideoFile, max_frames: Optional[int] = None) -> List[ImageFrame]:
        """
        Extract frames from video file using OpenCV.
        
        Args:
            video_file: Video file to process
            max_frames: Maximum number of frames to extract (default: self.max_frames)
            
        Returns:
            List of extracted image frames
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video file is corrupted or unreadable
        """
        if not os.path.exists(video_file.file_path):
            raise FileNotFoundError(f"Video file not found: {video_file.file_path}")
            
        max_frames = max_frames or self.max_frames
        frames = []
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_file.file_path)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_file.file_path}")
                
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Calculate frame extraction interval
            if duration > 0 and max_frames > 0:
                frame_step = max(1, int(fps * self.frame_interval))
                if total_frames > max_frames * frame_step:
                    frame_step = total_frames // max_frames
            else:
                frame_step = 1
                
            frame_count = 0
            extracted_count = 0
            
            while extracted_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Extract frame at intervals
                if frame_count % frame_step == 0:
                    # Save frame to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        temp_path = temp_file.name
                        
                    # Write frame to temporary file
                    success = cv2.imwrite(temp_path, frame)
                    if success:
                        timestamp = frame_count / fps if fps > 0 else 0
                        height, width = frame.shape[:2]
                        
                        image_frame = ImageFrame(
                            file_path=temp_path,
                            timestamp=timestamp,
                            resolution=(width, height)
                        )
                        frames.append(image_frame)
                        extracted_count += 1
                        
                        logger.debug(f"Extracted frame {extracted_count} at {timestamp:.2f}s")
                    else:
                        logger.warning(f"Failed to save frame {frame_count}")
                        
                frame_count += 1
                
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from video {video_file.file_path}")
            
        except Exception as e:
            logger.error(f"Error extracting frames from {video_file.file_path}: {str(e)}")
            raise ValueError(f"Frame extraction failed: {str(e)}")
            
        return frames
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image file to base64 string for OpenAI API.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_frame_with_gpt4v(self, image_frame: ImageFrame) -> Dict[str, any]:
        """
        Analyze a single frame using GPT-4V for visual content analysis.
        
        Args:
            image_frame: Image frame to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Encode image to base64
            base64_image = self._encode_image_to_base64(image_frame.file_path)
            
            # Prepare prompt for comprehensive visual analysis
            prompt = """Analyze this image frame and extract the following information:
            1. Objects and items visible in the frame
            2. Any text overlays, captions, or readable text
            3. Scene description and context
            4. People, faces, or human activities
            5. Brands, logos, or commercial elements
            6. Location indicators or environmental context
            
            Provide the response in a structured format with confidence levels for each detection."""
            
            # Call GPT-4V API
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the response to extract structured information
            analysis_result = self._parse_gpt4v_response(analysis_text, image_frame.timestamp)
            
            logger.debug(f"Analyzed frame at {image_frame.timestamp:.2f}s")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing frame {image_frame.file_path}: {str(e)}")
            return {
                "objects": [],
                "text_overlays": [],
                "scene_description": f"Analysis failed: {str(e)}",
                "confidence": 0.0,
                "timestamp": image_frame.timestamp
            }
    
    def _parse_gpt4v_response(self, response_text: str, timestamp: Optional[float] = None) -> Dict[str, any]:
        """
        Parse GPT-4V response text into structured data.
        
        Args:
            response_text: Raw response from GPT-4V
            timestamp: Frame timestamp
            
        Returns:
            Structured analysis data
        """
        # Simple parsing - in production, this could be more sophisticated
        # or use structured output from GPT-4
        
        objects = []
        text_overlays = []
        scene_description = response_text
        
        # Extract objects (look for common patterns)
        lines = response_text.lower().split('\n')
        confidence_indicators = 0
        total_lines = len([line for line in lines if line.strip()])
        
        for line in lines:
            if 'object' in line or 'item' in line:
                # Extract object mentions
                words = line.split()
                for word in words:
                    if len(word) > 3 and word.isalpha():
                        objects.append(word.capitalize())
                        
            if 'text' in line or 'overlay' in line or 'caption' in line:
                # Extract text overlay mentions
                if ':' in line:
                    text_part = line.split(':', 1)[1].strip()
                    if text_part:
                        text_overlays.append(text_part)
            
            # Look for confidence indicators in the response
            if any(indicator in line for indicator in ['clear', 'visible', 'obvious', 'definitely', 'certainly']):
                confidence_indicators += 1
        
        # Remove duplicates
        objects = list(set(objects))
        text_overlays = list(set(text_overlays))
        
        # Calculate confidence based on response quality
        base_confidence = 0.6  # Base confidence for GPT-4V
        
        # Adjust based on content richness
        if objects or text_overlays:
            content_bonus = min(0.2, (len(objects) + len(text_overlays)) * 0.05)
        else:
            content_bonus = -0.2  # Penalty for no detected content
        
        # Adjust based on confidence indicators in text
        if total_lines > 0:
            confidence_ratio = confidence_indicators / total_lines
            confidence_bonus = confidence_ratio * 0.2
        else:
            confidence_bonus = 0
        
        # Adjust based on response length (longer responses often indicate more detail)
        length_bonus = min(0.1, len(response_text) / 1000 * 0.1)
        
        final_confidence = max(0.1, min(1.0, base_confidence + content_bonus + confidence_bonus + length_bonus))
        
        return {
            "objects": objects[:10],  # Limit to top 10
            "text_overlays": text_overlays[:5],  # Limit to top 5
            "scene_description": scene_description,
            "confidence": final_confidence,
            "timestamp": timestamp,
            "confidence_factors": {
                "base": base_confidence,
                "content_bonus": content_bonus,
                "confidence_indicators": confidence_bonus,
                "length_bonus": length_bonus
            }
        }
    
    def process_video(self, video_file: VideoFile) -> VideoAnalysis:
        """
        Process video file to extract frames and perform visual analysis.
        
        Args:
            video_file: Video file to process
            
        Returns:
            Complete video analysis results
        """
        logger.info(f"Starting video processing for {video_file.file_path}")
        
        try:
            # Extract frames from video
            frames = self.extract_frames(video_file)
            
            if not frames:
                logger.warning(f"No frames extracted from {video_file.file_path}")
                return VideoAnalysis(
                    content_id="",
                    frame_count=0,
                    detected_objects=[],
                    text_overlays=[],
                    scene_descriptions=["No frames could be extracted"],
                    confidence_scores={
                        "overall": 0.0,
                        "frame_extraction": 0.0,
                        "object_detection": 0.0,
                        "text_recognition": 0.0,
                        "scene_analysis": 0.0
                    }
                )
            
            # Analyze each frame with GPT-4V
            all_objects = []
            all_text_overlays = []
            scene_descriptions = []
            confidence_scores = {}
            frame_analysis_results = []
            
            successful_analyses = 0
            
            for i, frame in enumerate(frames):
                try:
                    analysis = self.analyze_frame_with_gpt4v(frame)
                    
                    all_objects.extend(analysis.get("objects", []))
                    all_text_overlays.extend(analysis.get("text_overlays", []))
                    scene_descriptions.append(analysis.get("scene_description", ""))
                    confidence_scores[f"frame_{i}"] = analysis.get("confidence", 0.0)
                    frame_analysis_results.append(analysis)
                    successful_analyses += 1
                    
                except Exception as e:
                    logger.error(f"Failed to analyze frame {i}: {str(e)}")
                    confidence_scores[f"frame_{i}"] = 0.0
                
                finally:
                    # Clean up temporary frame file
                    try:
                        os.unlink(frame.file_path)
                    except OSError:
                        pass
            
            # Aggregate results
            unique_objects = list(set(all_objects))
            unique_text_overlays = list(set(all_text_overlays))
            
            # Calculate detailed confidence scores
            detailed_confidence_scores = self._calculate_video_confidence_scores(
                frames, frame_analysis_results, unique_objects, unique_text_overlays, 
                scene_descriptions, successful_analyses
            )
            
            logger.info(f"Video processing completed. Found {len(unique_objects)} objects, "
                       f"{len(unique_text_overlays)} text overlays, "
                       f"overall confidence: {detailed_confidence_scores.get('overall', 0.0):.2f}")
            
            return VideoAnalysis(
                content_id="",  # Will be set by caller
                frame_count=len(frames),
                detected_objects=unique_objects,
                text_overlays=unique_text_overlays,
                scene_descriptions=scene_descriptions,
                confidence_scores=detailed_confidence_scores
            )
            
        except Exception as e:
            logger.error(f"Video processing failed for {video_file.file_path}: {str(e)}")
            raise
    
    def _calculate_video_confidence_scores(self, frames: List[ImageFrame], 
                                         frame_analyses: List[Dict], objects: List[str], 
                                         text_overlays: List[str], scene_descriptions: List[str],
                                         successful_analyses: int) -> Dict[str, float]:
        """
        Calculate detailed confidence scores for video analysis.
        
        Args:
            frames: List of extracted frames
            frame_analyses: List of frame analysis results
            objects: Detected objects across all frames
            text_overlays: Detected text overlays
            scene_descriptions: Scene descriptions from all frames
            successful_analyses: Number of successful frame analyses
            
        Returns:
            Dictionary of confidence scores
        """
        confidence_scores = {}
        
        # Frame extraction confidence
        if len(frames) > 0:
            confidence_scores["frame_extraction"] = 1.0  # Successful if we got frames
        else:
            confidence_scores["frame_extraction"] = 0.0
        
        # Analysis success rate
        if len(frames) > 0:
            analysis_success_rate = successful_analyses / len(frames)
            confidence_scores["analysis_success_rate"] = analysis_success_rate
        else:
            confidence_scores["analysis_success_rate"] = 0.0
        
        # Object detection confidence
        if frame_analyses:
            object_confidences = []
            for analysis in frame_analyses:
                if analysis.get("objects"):
                    # Higher confidence if objects detected
                    object_confidences.append(analysis.get("confidence", 0.0))
                else:
                    # Lower confidence if no objects detected
                    object_confidences.append(analysis.get("confidence", 0.0) * 0.5)
            
            if object_confidences:
                confidence_scores["object_detection"] = sum(object_confidences) / len(object_confidences)
            else:
                confidence_scores["object_detection"] = 0.0
        else:
            confidence_scores["object_detection"] = 0.0
        
        # Text recognition confidence
        if frame_analyses:
            text_confidences = []
            for analysis in frame_analyses:
                if analysis.get("text_overlays"):
                    # Higher confidence if text detected
                    text_confidences.append(analysis.get("confidence", 0.0))
                else:
                    # Neutral confidence if no text (text might not be present)
                    text_confidences.append(analysis.get("confidence", 0.0) * 0.8)
            
            if text_confidences:
                confidence_scores["text_recognition"] = sum(text_confidences) / len(text_confidences)
            else:
                confidence_scores["text_recognition"] = 0.0
        else:
            confidence_scores["text_recognition"] = 0.0
        
        # Scene analysis confidence (based on description quality)
        if scene_descriptions:
            scene_confidences = []
            for i, description in enumerate(scene_descriptions):
                if description and len(description.strip()) > 20:
                    # Good description length indicates better analysis
                    base_conf = frame_analyses[i].get("confidence", 0.0) if i < len(frame_analyses) else 0.5
                    scene_confidences.append(base_conf)
                else:
                    scene_confidences.append(0.3)  # Low confidence for poor descriptions
            
            confidence_scores["scene_analysis"] = sum(scene_confidences) / len(scene_confidences)
        else:
            confidence_scores["scene_analysis"] = 0.0
        
        # Overall confidence (weighted average)
        weights = {
            "frame_extraction": 0.1,
            "analysis_success_rate": 0.2,
            "object_detection": 0.3,
            "text_recognition": 0.2,
            "scene_analysis": 0.2
        }
        
        overall_confidence = 0.0
        for component, weight in weights.items():
            overall_confidence += confidence_scores.get(component, 0.0) * weight
        
        confidence_scores["overall"] = overall_confidence
        
        # Add frame-level confidences for reference
        for i, analysis in enumerate(frame_analyses):
            confidence_scores[f"frame_{i}"] = analysis.get("confidence", 0.0)
        
        return confidence_scores

    def cleanup_temp_files(self, frames: List[ImageFrame]) -> None:
        """
        Clean up temporary frame files.
        
        Args:
            frames: List of image frames to clean up
        """
        for frame in frames:
            try:
                if os.path.exists(frame.file_path):
                    os.unlink(frame.file_path)
            except OSError as e:
                logger.warning(f"Failed to delete temporary file {frame.file_path}: {str(e)}")