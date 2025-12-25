"""
Multi-Modal Analysis Pipeline for processing different content types.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.models.analysis import (
    VideoAnalysis, AudioTranscription, TextAnalysis, VisionAnalysis, 
    ContentAnalysis, Entity
)
from src.models.content import VideoFile, AudioFile, ImageFrame
from src.analysis.video_processor import VideoProcessor
from src.analysis.audio_processor import AudioProcessor
from src.analysis.text_processor import TextProcessor

logger = logging.getLogger(__name__)


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
    
    def process_complete_content(self, video_file: Optional[VideoFile] = None,
                               audio_file: Optional[AudioFile] = None,
                               text_content: Optional[str] = None,
                               content_id: str = "") -> ContentAnalysis:
        """
        Process complete multi-modal content and integrate confidence scores.
        
        Args:
            video_file: Optional video file to process
            audio_file: Optional audio file to process (if separate from video)
            text_content: Optional text content (captions, hashtags)
            content_id: Content identifier
            
        Returns:
            Complete content analysis with integrated confidence scores
        """
        logger.info(f"Starting complete multi-modal analysis for content {content_id}")
        
        # Initialize analysis results
        text_analysis = None
        video_analysis = None
        audio_analysis = None
        all_entities = []
        
        try:
            # Process text content
            if text_content:
                logger.info("Processing text content...")
                text_analysis = self.process_text(text_content)
                text_analysis.content_id = content_id
                all_entities.extend(text_analysis.extracted_entities)
            
            # Process video content
            if video_file:
                logger.info("Processing video content...")
                video_analysis = self.process_video(video_file)
                video_analysis.content_id = content_id
                
                # Also extract audio from video
                logger.info("Processing audio from video...")
                audio_analysis = self.process_video_audio(video_file)
                audio_analysis.content_id = content_id
            
            # Process separate audio file if provided
            elif audio_file:
                logger.info("Processing separate audio file...")
                audio_analysis = self.process_audio(audio_file)
                audio_analysis.content_id = content_id
            
            # Integrate confidence scores across all modalities
            integrated_confidence_scores = self._integrate_confidence_scores(
                text_analysis, video_analysis, audio_analysis
            )
            
            # Merge entities from all sources and remove duplicates
            unique_entities = self._merge_entities(all_entities)
            
            logger.info(f"Multi-modal analysis completed for {content_id}. "
                       f"Found {len(unique_entities)} unique entities, "
                       f"overall confidence: {integrated_confidence_scores.get('overall', 0.0):.2f}")
            
            return ContentAnalysis(
                content_id=content_id,
                text_analysis=text_analysis,
                vision_analysis=None,  # TODO: Implement when vision analysis is added
                audio_analysis=audio_analysis,
                extracted_entities=unique_entities,
                confidence_scores=integrated_confidence_scores
            )
            
        except Exception as e:
            logger.error(f"Multi-modal analysis failed for {content_id}: {str(e)}")
            return ContentAnalysis(
                content_id=content_id,
                text_analysis=text_analysis,
                vision_analysis=None,
                audio_analysis=audio_analysis,
                extracted_entities=all_entities,
                confidence_scores={"overall": 0.0, "error": str(e)}
            )
    
    def _integrate_confidence_scores(self, text_analysis: Optional[TextAnalysis],
                                   video_analysis: Optional[VideoAnalysis],
                                   audio_analysis: Optional[AudioTranscription]) -> Dict[str, float]:
        """
        Integrate confidence scores from all analysis modalities.
        
        Args:
            text_analysis: Text analysis results
            video_analysis: Video analysis results
            audio_analysis: Audio analysis results
            
        Returns:
            Integrated confidence scores
        """
        integrated_scores = {}
        modality_weights = {}
        
        # Collect confidence scores from each modality
        if text_analysis and text_analysis.confidence_scores:
            integrated_scores["text"] = text_analysis.confidence_scores.get("overall", 0.0)
            modality_weights["text"] = 0.4  # Text is often most reliable
            
            # Include detailed text scores
            for key, value in text_analysis.confidence_scores.items():
                if key != "overall":
                    integrated_scores[f"text_{key}"] = value
        
        if video_analysis and video_analysis.confidence_scores:
            integrated_scores["video"] = video_analysis.confidence_scores.get("overall", 0.0)
            modality_weights["video"] = 0.35  # Video provides rich visual information
            
            # Include detailed video scores
            for key, value in video_analysis.confidence_scores.items():
                if key != "overall" and not key.startswith("frame_"):
                    integrated_scores[f"video_{key}"] = value
        
        if audio_analysis and hasattr(audio_analysis, 'confidence'):
            integrated_scores["audio"] = audio_analysis.confidence
            modality_weights["audio"] = 0.25  # Audio transcription can be less reliable
        
        # Calculate overall confidence as weighted average of available modalities
        if modality_weights:
            total_weight = sum(modality_weights.values())
            overall_confidence = 0.0
            
            for modality, weight in modality_weights.items():
                normalized_weight = weight / total_weight
                overall_confidence += integrated_scores.get(modality, 0.0) * normalized_weight
            
            integrated_scores["overall"] = overall_confidence
        else:
            integrated_scores["overall"] = 0.0
        
        # Add cross-modal consistency scores
        integrated_scores.update(self._calculate_cross_modal_consistency(
            text_analysis, video_analysis, audio_analysis
        ))
        
        return integrated_scores
    
    def _calculate_cross_modal_consistency(self, text_analysis: Optional[TextAnalysis],
                                         video_analysis: Optional[VideoAnalysis],
                                         audio_analysis: Optional[AudioTranscription]) -> Dict[str, float]:
        """
        Calculate consistency scores between different modalities.
        
        Args:
            text_analysis: Text analysis results
            video_analysis: Video analysis results
            audio_analysis: Audio analysis results
            
        Returns:
            Cross-modal consistency scores
        """
        consistency_scores = {}
        
        # Text-Video consistency (check if text mentions align with visual content)
        if text_analysis and video_analysis:
            text_entities = {entity.name.lower() for entity in text_analysis.extracted_entities}
            video_objects = {obj.lower() for obj in video_analysis.detected_objects}
            
            if text_entities and video_objects:
                overlap = len(text_entities.intersection(video_objects))
                total_unique = len(text_entities.union(video_objects))
                consistency_scores["text_video_consistency"] = overlap / total_unique if total_unique > 0 else 0.0
            else:
                consistency_scores["text_video_consistency"] = 0.5  # Neutral when no entities
        
        # Text-Audio consistency (check if text content aligns with audio transcript)
        if text_analysis and audio_analysis:
            if audio_analysis.transcript and len(audio_analysis.transcript.strip()) > 10:
                # Simple keyword overlap check
                text_keywords = set(text_analysis.keywords) if text_analysis.keywords else set()
                audio_words = set(audio_analysis.transcript.lower().split())
                
                if text_keywords and audio_words:
                    overlap = len(text_keywords.intersection(audio_words))
                    consistency_scores["text_audio_consistency"] = min(1.0, overlap / len(text_keywords))
                else:
                    consistency_scores["text_audio_consistency"] = 0.5
            else:
                consistency_scores["text_audio_consistency"] = 0.3  # Low confidence for poor audio
        
        # Video-Audio consistency (check if visual content aligns with audio)
        if video_analysis and audio_analysis:
            # This is more complex - for now, just check if both have content
            has_video_content = len(video_analysis.detected_objects) > 0 or len(video_analysis.text_overlays) > 0
            has_audio_content = len(audio_analysis.transcript.strip()) > 10 if audio_analysis.transcript else False
            
            if has_video_content and has_audio_content:
                consistency_scores["video_audio_consistency"] = 0.8  # Both have content
            elif has_video_content or has_audio_content:
                consistency_scores["video_audio_consistency"] = 0.6  # One has content
            else:
                consistency_scores["video_audio_consistency"] = 0.4  # Neither has much content
        
        return consistency_scores
    
    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Merge entities from different sources, removing duplicates and combining confidence.
        
        Args:
            entities: List of entities from all sources
            
        Returns:
            List of unique entities with merged confidence scores
        """
        if not entities:
            return []
        
        # Group entities by name and category
        entity_groups = {}
        
        for entity in entities:
            key = (entity.name.lower().strip(), entity.category)
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)
        
        # Merge entities in each group
        merged_entities = []
        
        for (name, category), group in entity_groups.items():
            if len(group) == 1:
                # Single entity, use as-is
                merged_entities.append(group[0])
            else:
                # Multiple entities with same name/category - merge them
                # Use the entity with highest confidence as base
                best_entity = max(group, key=lambda e: e.confidence)
                
                # Calculate merged confidence (average with boost for multiple sources)
                avg_confidence = sum(e.confidence for e in group) / len(group)
                # Boost confidence slightly for cross-modal confirmation
                boost_factor = min(1.2, 1.0 + (len(group) - 1) * 0.1)
                merged_confidence = min(1.0, avg_confidence * boost_factor)
                
                # Combine contexts
                contexts = [e.context for e in group if e.context]
                merged_context = "; ".join(contexts[:3])  # Limit to avoid too long context
                
                # Create merged entity
                merged_entity = Entity(
                    name=best_entity.name,  # Use the name from best entity (might have better capitalization)
                    category=category,
                    confidence=merged_confidence,
                    source=best_entity.source,  # Use source from best entity
                    context=merged_context
                )
                
                merged_entities.append(merged_entity)
        
        # Sort by confidence (highest first)
        merged_entities.sort(key=lambda e: e.confidence, reverse=True)
        
        return merged_entities