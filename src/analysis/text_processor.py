"""
Text processing module for caption and hashtag analysis.
"""

import logging
import re
from typing import List, Dict, Optional, Set
from openai import OpenAI

from src.models.analysis import TextAnalysis, Entity, EntityCategory, EntitySource
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Processes text content from captions and hashtags to extract entities and categorize content.
    
    Uses OpenAI GPT models for entity extraction and content categorization.
    Implements requirements 3.3 and 3.4: Extract entities, locations, and recommendations from captions and comments,
    and categorize content by topic and intent from hashtags.
    """
    
    def __init__(self):
        """Initialize the text processor with OpenAI client."""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        
        # Common hashtag categories for content classification
        self.hashtag_categories = {
            'food': ['food', 'foodie', 'recipe', 'cooking', 'restaurant', 'cafe', 'dinner', 'lunch', 'breakfast'],
            'travel': ['travel', 'vacation', 'trip', 'explore', 'wanderlust', 'adventure', 'destination'],
            'fashion': ['fashion', 'style', 'outfit', 'ootd', 'clothing', 'accessories', 'shoes'],
            'beauty': ['beauty', 'makeup', 'skincare', 'cosmetics', 'hair', 'nails'],
            'fitness': ['fitness', 'workout', 'gym', 'health', 'exercise', 'training', 'yoga'],
            'lifestyle': ['lifestyle', 'daily', 'life', 'home', 'decor', 'inspiration'],
            'business': ['business', 'entrepreneur', 'startup', 'work', 'career', 'professional'],
            'technology': ['tech', 'technology', 'gadget', 'app', 'software', 'digital'],
            'art': ['art', 'artist', 'creative', 'design', 'photography', 'drawing', 'painting'],
            'music': ['music', 'song', 'artist', 'concert', 'album', 'musician'],
            'education': ['education', 'learning', 'study', 'school', 'university', 'knowledge'],
            'entertainment': ['entertainment', 'movie', 'tv', 'show', 'celebrity', 'fun']
        }
    
    def extract_hashtags(self, text: str) -> List[str]:
        """
        Extract hashtags from text content.
        
        Args:
            text: Text content to extract hashtags from
            
        Returns:
            List of hashtags (without # symbol)
        """
        if not text:
            return []
            
        # Find all hashtags using regex
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text.lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for hashtag in hashtags:
            if hashtag not in seen:
                seen.add(hashtag)
                unique_hashtags.append(hashtag)
        
        logger.debug(f"Extracted {len(unique_hashtags)} hashtags from text")
        return unique_hashtags
    
    def categorize_hashtags(self, hashtags: List[str]) -> Dict[str, List[str]]:
        """
        Categorize hashtags by topic/intent.
        
        Args:
            hashtags: List of hashtags to categorize
            
        Returns:
            Dictionary mapping categories to matching hashtags
        """
        if not hashtags:
            return {}
            
        categorized = {}
        
        for category, keywords in self.hashtag_categories.items():
            matching_hashtags = []
            
            for hashtag in hashtags:
                # Check if hashtag matches any keyword in the category
                for keyword in keywords:
                    if keyword in hashtag or hashtag in keyword:
                        matching_hashtags.append(hashtag)
                        break
            
            if matching_hashtags:
                categorized[category] = matching_hashtags
        
        # Add uncategorized hashtags
        categorized_hashtags = set()
        for hashtag_list in categorized.values():
            categorized_hashtags.update(hashtag_list)
        
        uncategorized = [h for h in hashtags if h not in categorized_hashtags]
        if uncategorized:
            categorized['other'] = uncategorized
        
        logger.debug(f"Categorized hashtags into {len(categorized)} categories")
        return categorized
    
    def extract_entities_with_gpt(self, text: str, source: EntitySource) -> List[Entity]:
        """
        Extract entities from text using OpenAI GPT models.
        
        Args:
            text: Text content to analyze
            source: Source of the text (caption, hashtag, etc.)
            
        Returns:
            List of extracted entities
        """
        if not text or not text.strip():
            return []
            
        logger.debug(f"Extracting entities from {source.value} text: {text[:100]}...")
        
        try:
            # Prepare prompt for entity extraction
            prompt = f"""Analyze the following Instagram {source.value} text and extract entities with their categories and confidence scores.

Text: "{text}"

Extract entities in the following categories:
- PRODUCT: Specific products, brands, items mentioned
- LOCATION: Places, cities, countries, venues, restaurants
- PERSON: People mentioned (excluding generic terms)
- CONCEPT: Abstract concepts, topics, themes
- BRAND: Company names, brand names
- EVENT: Events, occasions, activities

For each entity, provide:
1. Entity name (normalized form)
2. Category (from the list above)
3. Confidence score (0.0-1.0)
4. Context (the surrounding text where it was found)

Format your response as a JSON array of objects with fields: name, category, confidence, context.
Only include entities you are confident about (confidence > 0.6).
Limit to maximum 10 entities per text."""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for better entity extraction
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured information from social media content. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            entities = self._parse_gpt_entity_response(response_text, source, text)
            
            logger.debug(f"Extracted {len(entities)} entities from {source.value}")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed for {source.value}: {str(e)}")
            return []
    
    def _parse_gpt_entity_response(self, response_text: str, source: EntitySource, original_text: str) -> List[Entity]:
        """
        Parse GPT response to extract entities.
        
        Args:
            response_text: Raw response from GPT
            source: Source of the text
            original_text: Original text for context
            
        Returns:
            List of Entity objects
        """
        entities = []
        
        try:
            import json
            
            # Try to extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                entity_data = json.loads(json_text)
                
                for item in entity_data:
                    try:
                        # Validate required fields
                        if not all(key in item for key in ['name', 'category', 'confidence']):
                            continue
                            
                        # Map category string to enum
                        category_map = {
                            'PRODUCT': EntityCategory.PRODUCT,
                            'LOCATION': EntityCategory.LOCATION,
                            'PERSON': EntityCategory.PERSON,
                            'CONCEPT': EntityCategory.CONCEPT,
                            'BRAND': EntityCategory.BRAND,
                            'EVENT': EntityCategory.EVENT
                        }
                        
                        category = category_map.get(item['category'].upper())
                        if not category:
                            continue
                            
                        # Validate confidence score
                        confidence = float(item['confidence'])
                        if confidence < 0.6 or confidence > 1.0:
                            continue
                            
                        # Create entity
                        entity = Entity(
                            name=item['name'].strip(),
                            category=category,
                            confidence=confidence,
                            source=source,
                            context=item.get('context', original_text[:100])
                        )
                        
                        entities.append(entity)
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid entity data: {item}, error: {str(e)}")
                        continue
                        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GPT response as JSON: {str(e)}")
            # Fallback to simple text parsing
            entities = self._fallback_entity_extraction(response_text, source, original_text)
            
        except Exception as e:
            logger.error(f"Error parsing GPT entity response: {str(e)}")
            
        return entities
    
    def _fallback_entity_extraction(self, response_text: str, source: EntitySource, original_text: str) -> List[Entity]:
        """
        Fallback entity extraction when JSON parsing fails.
        
        Args:
            response_text: Raw response text
            source: Source of the text
            original_text: Original text for context
            
        Returns:
            List of Entity objects
        """
        entities = []
        
        # Simple pattern matching for common entities
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Look for patterns like "Product: iPhone (0.9)"
            patterns = [
                r'(Product|PRODUCT):\s*([^(]+)\s*\(([0-9.]+)\)',
                r'(Location|LOCATION):\s*([^(]+)\s*\(([0-9.]+)\)',
                r'(Brand|BRAND):\s*([^(]+)\s*\(([0-9.]+)\)',
                r'(Person|PERSON):\s*([^(]+)\s*\(([0-9.]+)\)',
                r'(Concept|CONCEPT):\s*([^(]+)\s*\(([0-9.]+)\)',
                r'(Event|EVENT):\s*([^(]+)\s*\(([0-9.]+)\)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    category_str = match.group(1).upper()
                    name = match.group(2).strip()
                    confidence = float(match.group(3))
                    
                    if confidence >= 0.6:
                        category_map = {
                            'PRODUCT': EntityCategory.PRODUCT,
                            'LOCATION': EntityCategory.LOCATION,
                            'PERSON': EntityCategory.PERSON,
                            'CONCEPT': EntityCategory.CONCEPT,
                            'BRAND': EntityCategory.BRAND,
                            'EVENT': EntityCategory.EVENT
                        }
                        
                        category = category_map.get(category_str)
                        if category:
                            entity = Entity(
                                name=name,
                                category=category,
                                confidence=confidence,
                                source=source,
                                context=original_text[:100]
                            )
                            entities.append(entity)
                    break
        
        return entities
    
    def analyze_caption(self, caption: str) -> TextAnalysis:
        """
        Analyze Instagram caption text to extract entities and topics.
        
        Args:
            caption: Caption text to analyze
            
        Returns:
            TextAnalysis with extracted information
        """
        logger.info(f"Analyzing caption: {caption[:100]}...")
        
        if not caption or not caption.strip():
            return TextAnalysis(
                content_id="",
                extracted_entities=[],
                sentiment=None,
                topics=[],
                keywords=[]
            )
        
        try:
            # Extract hashtags from caption
            hashtags = self.extract_hashtags(caption)
            
            # Categorize hashtags
            hashtag_categories = self.categorize_hashtags(hashtags)
            
            # Extract entities from caption text (excluding hashtags)
            caption_text = re.sub(r'#\w+', '', caption).strip()
            caption_entities = self.extract_entities_with_gpt(caption_text, EntitySource.CAPTION)
            
            # Extract entities from hashtags
            hashtag_entities = []
            for hashtag in hashtags:
                hashtag_entities.extend(
                    self.extract_entities_with_gpt(f"#{hashtag}", EntitySource.HASHTAG)
                )
            
            # Combine all entities
            all_entities = caption_entities + hashtag_entities
            
            # Remove duplicate entities (same name and category)
            unique_entities = []
            seen = set()
            for entity in all_entities:
                key = (entity.name.lower(), entity.category)
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
            
            # Extract topics from hashtag categories
            topics = list(hashtag_categories.keys())
            
            # Extract keywords (simple approach - could be enhanced)
            keywords = self._extract_keywords(caption_text)
            
            logger.info(f"Caption analysis completed: {len(unique_entities)} entities, "
                       f"{len(topics)} topics, {len(keywords)} keywords")
            
            return TextAnalysis(
                content_id="",  # Will be set by caller
                extracted_entities=unique_entities,
                sentiment=None,  # Could be added later
                topics=topics,
                keywords=keywords
            )
            
        except Exception as e:
            logger.error(f"Caption analysis failed: {str(e)}")
            return TextAnalysis(
                content_id="",
                extracted_entities=[],
                sentiment=None,
                topics=[],
                keywords=[]
            )
    
    def analyze_hashtags(self, hashtags: List[str]) -> Dict[str, any]:
        """
        Analyze hashtags to categorize content and extract topics.
        
        Args:
            hashtags: List of hashtags to analyze
            
        Returns:
            Dictionary with categorization results
        """
        logger.info(f"Analyzing {len(hashtags)} hashtags")
        
        if not hashtags:
            return {
                'categories': {},
                'topics': [],
                'entities': []
            }
        
        try:
            # Categorize hashtags
            categories = self.categorize_hashtags(hashtags)
            
            # Extract entities from hashtags
            entities = []
            for hashtag in hashtags:
                hashtag_entities = self.extract_entities_with_gpt(f"#{hashtag}", EntitySource.HASHTAG)
                entities.extend(hashtag_entities)
            
            # Remove duplicate entities
            unique_entities = []
            seen = set()
            for entity in entities:
                key = (entity.name.lower(), entity.category)
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
            
            # Extract topics
            topics = list(categories.keys())
            
            logger.info(f"Hashtag analysis completed: {len(categories)} categories, "
                       f"{len(unique_entities)} entities")
            
            return {
                'categories': categories,
                'topics': topics,
                'entities': unique_entities
            }
            
        except Exception as e:
            logger.error(f"Hashtag analysis failed: {str(e)}")
            return {
                'categories': {},
                'topics': [],
                'entities': []
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text using simple heuristics.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        # Simple keyword extraction - could be enhanced with NLP libraries
        # Remove common stop words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those',
            'over'
        }
        
        # Clean text and split into words
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Filter out stop words and short words
        keywords = []
        for word in words:
            if len(word) > 3 and word not in stop_words and word.isalpha():
                keywords.append(word)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        # Limit to top 10 keywords
        return unique_keywords[:10]
    
    def process_text_content(self, caption: str, hashtags: List[str] = None) -> TextAnalysis:
        """
        Process complete text content including caption and hashtags.
        
        Args:
            caption: Caption text
            hashtags: List of hashtags (optional, will be extracted from caption if not provided)
            
        Returns:
            Complete TextAnalysis results
        """
        logger.info(f"Processing text content: caption length {len(caption)}, "
                   f"{len(hashtags) if hashtags else 'auto-detect'} hashtags")
        
        try:
            # If hashtags not provided, extract from caption
            if hashtags is None:
                hashtags = self.extract_hashtags(caption)
            
            # Analyze caption
            caption_analysis = self.analyze_caption(caption)
            
            # Analyze hashtags separately for additional insights
            hashtag_analysis = self.analyze_hashtags(hashtags)
            
            # Combine results
            all_entities = caption_analysis.extracted_entities + hashtag_analysis['entities']
            
            # Remove duplicate entities
            unique_entities = []
            seen = set()
            for entity in all_entities:
                key = (entity.name.lower(), entity.category)
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
            
            # Combine topics
            all_topics = list(set(caption_analysis.topics + hashtag_analysis['topics']))
            
            logger.info(f"Text processing completed: {len(unique_entities)} entities, "
                       f"{len(all_topics)} topics")
            
            return TextAnalysis(
                content_id="",  # Will be set by caller
                extracted_entities=unique_entities,
                sentiment=caption_analysis.sentiment,
                topics=all_topics,
                keywords=caption_analysis.keywords
            )
            
        except Exception as e:
            logger.error(f"Text content processing failed: {str(e)}")
            return TextAnalysis(
                content_id="",
                extracted_entities=[],
                sentiment=None,
                topics=[],
                keywords=[]
            )