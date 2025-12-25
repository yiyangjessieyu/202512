"""
Tests for TextProcessor functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.analysis.text_processor import TextProcessor
from src.models.analysis import TextAnalysis, Entity, EntityCategory, EntitySource


class TestTextProcessor:
    """Test cases for TextProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TextProcessor()
    
    def test_extract_hashtags_basic(self):
        """Test basic hashtag extraction."""
        text = "Love this #food #restaurant #delicious meal! #yummy"
        hashtags = self.processor.extract_hashtags(text)
        
        expected = ['food', 'restaurant', 'delicious', 'yummy']
        assert hashtags == expected
    
    def test_extract_hashtags_empty_text(self):
        """Test hashtag extraction with empty text."""
        assert self.processor.extract_hashtags("") == []
        assert self.processor.extract_hashtags(None) == []
    
    def test_extract_hashtags_no_hashtags(self):
        """Test text without hashtags."""
        text = "This is just regular text without any hashtags."
        hashtags = self.processor.extract_hashtags(text)
        assert hashtags == []
    
    def test_extract_hashtags_duplicates(self):
        """Test hashtag extraction with duplicates."""
        text = "Great #food at this #restaurant! The #food was amazing. #Food #FOOD"
        hashtags = self.processor.extract_hashtags(text)
        
        # Should remove duplicates and normalize to lowercase
        assert hashtags == ['food', 'restaurant']
    
    def test_categorize_hashtags_food(self):
        """Test hashtag categorization for food category."""
        hashtags = ['food', 'restaurant', 'delicious', 'cooking', 'recipe']
        categories = self.processor.categorize_hashtags(hashtags)
        
        assert 'food' in categories
        assert 'food' in categories['food']
        assert 'restaurant' in categories['food']
        assert 'cooking' in categories['food']
        assert 'recipe' in categories['food']
    
    def test_categorize_hashtags_multiple_categories(self):
        """Test hashtag categorization across multiple categories."""
        hashtags = ['travel', 'food', 'fashion', 'workout', 'photography']
        categories = self.processor.categorize_hashtags(hashtags)
        
        assert 'travel' in categories
        assert 'food' in categories
        assert 'fashion' in categories
        assert 'fitness' in categories
        assert 'art' in categories
    
    def test_categorize_hashtags_uncategorized(self):
        """Test hashtags that don't fit known categories."""
        hashtags = ['randomtag', 'uniquehashtag', 'unknowncategory']
        categories = self.processor.categorize_hashtags(hashtags)
        
        assert 'other' in categories
        assert all(tag in categories['other'] for tag in hashtags)
    
    def test_categorize_hashtags_empty(self):
        """Test categorization with empty hashtag list."""
        categories = self.processor.categorize_hashtags([])
        assert categories == {}
    
    @patch('src.analysis.text_processor.OpenAI')
    def test_extract_entities_with_gpt_success(self, mock_openai_class):
        """Test successful entity extraction with GPT."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''[
            {
                "name": "iPhone 15",
                "category": "PRODUCT",
                "confidence": 0.9,
                "context": "Just got the new iPhone 15"
            },
            {
                "name": "Apple",
                "category": "BRAND",
                "confidence": 0.8,
                "context": "Apple iPhone 15"
            }
        ]'''
        mock_client.chat.completions.create.return_value = mock_response
        
        processor = TextProcessor()
        text = "Just got the new iPhone 15 from Apple!"
        entities = processor.extract_entities_with_gpt(text, EntitySource.CAPTION)
        
        assert len(entities) == 2
        assert entities[0].name == "iPhone 15"
        assert entities[0].category == EntityCategory.PRODUCT
        assert entities[0].confidence == 0.9
        assert entities[0].source == EntitySource.CAPTION
        
        assert entities[1].name == "Apple"
        assert entities[1].category == EntityCategory.BRAND
        assert entities[1].confidence == 0.8
    
    @patch('src.analysis.text_processor.OpenAI')
    def test_extract_entities_with_gpt_api_error(self, mock_openai_class):
        """Test entity extraction with API error."""
        # Mock OpenAI to raise an exception
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        processor = TextProcessor()
        text = "Test text"
        entities = processor.extract_entities_with_gpt(text, EntitySource.CAPTION)
        
        # Should return empty list on error
        assert entities == []
    
    @patch('src.analysis.text_processor.OpenAI')
    def test_extract_entities_with_gpt_invalid_json(self, mock_openai_class):
        """Test entity extraction with invalid JSON response."""
        # Mock OpenAI response with invalid JSON
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        
        processor = TextProcessor()
        text = "Test text"
        entities = processor.extract_entities_with_gpt(text, EntitySource.CAPTION)
        
        # Should handle gracefully and return empty list or fallback results
        assert isinstance(entities, list)
    
    def test_extract_entities_empty_text(self):
        """Test entity extraction with empty text."""
        entities = self.processor.extract_entities_with_gpt("", EntitySource.CAPTION)
        assert entities == []
        
        entities = self.processor.extract_entities_with_gpt(None, EntitySource.CAPTION)
        assert entities == []
    
    @patch('src.analysis.text_processor.TextProcessor.extract_entities_with_gpt')
    @patch('src.analysis.text_processor.TextProcessor.extract_hashtags')
    def test_analyze_caption_success(self, mock_extract_hashtags, mock_extract_entities):
        """Test successful caption analysis."""
        # Mock dependencies
        mock_extract_hashtags.return_value = ['food', 'restaurant']
        mock_extract_entities.return_value = [
            Entity(
                name="Pizza Palace",
                category=EntityCategory.LOCATION,
                confidence=0.9,
                source=EntitySource.CAPTION,
                context="Great pizza at Pizza Palace"
            )
        ]
        
        caption = "Great pizza at Pizza Palace! #food #restaurant"
        result = self.processor.analyze_caption(caption)
        
        assert isinstance(result, TextAnalysis)
        assert len(result.extracted_entities) == 1
        assert result.extracted_entities[0].name == "Pizza Palace"
        assert 'food' in result.topics
    
    def test_analyze_caption_empty(self):
        """Test caption analysis with empty caption."""
        result = self.processor.analyze_caption("")
        
        assert isinstance(result, TextAnalysis)
        assert result.extracted_entities == []
        assert result.topics == []
        assert result.keywords == []
    
    @patch('src.analysis.text_processor.TextProcessor.extract_entities_with_gpt')
    def test_analyze_hashtags_success(self, mock_extract_entities):
        """Test successful hashtag analysis."""
        # Mock entity extraction
        mock_extract_entities.return_value = [
            Entity(
                name="Food",
                category=EntityCategory.CONCEPT,
                confidence=0.8,
                source=EntitySource.HASHTAG,
                context="#food"
            )
        ]
        
        hashtags = ['food', 'restaurant', 'delicious']
        result = self.processor.analyze_hashtags(hashtags)
        
        assert 'categories' in result
        assert 'topics' in result
        assert 'entities' in result
        assert 'food' in result['categories']
        assert len(result['entities']) == 1
    
    def test_analyze_hashtags_empty(self):
        """Test hashtag analysis with empty list."""
        result = self.processor.analyze_hashtags([])
        
        assert result['categories'] == {}
        assert result['topics'] == []
        assert result['entities'] == []
    
    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        text = "This is a great restaurant with amazing food and excellent service"
        keywords = self.processor._extract_keywords(text)
        
        # Should extract meaningful words, excluding stop words
        expected_words = ['great', 'restaurant', 'amazing', 'food', 'excellent', 'service']
        for word in expected_words:
            assert word in keywords
    
    def test_extract_keywords_empty_text(self):
        """Test keyword extraction with empty text."""
        assert self.processor._extract_keywords("") == []
        assert self.processor._extract_keywords(None) == []
    
    def test_extract_keywords_stop_words_filtered(self):
        """Test that stop words are filtered out."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = self.processor._extract_keywords(text)
        
        # Stop words should be filtered out
        stop_words = ['the', 'over']
        for stop_word in stop_words:
            assert stop_word not in keywords
        
        # Meaningful words should remain
        assert 'quick' in keywords
        assert 'brown' in keywords
        assert 'jumps' in keywords
    
    @patch('src.analysis.text_processor.TextProcessor.analyze_caption')
    @patch('src.analysis.text_processor.TextProcessor.analyze_hashtags')
    def test_process_text_content_success(self, mock_analyze_hashtags, mock_analyze_caption):
        """Test complete text content processing."""
        # Mock caption analysis
        mock_analyze_caption.return_value = TextAnalysis(
            content_id="",
            extracted_entities=[
                Entity(
                    name="Restaurant",
                    category=EntityCategory.LOCATION,
                    confidence=0.9,
                    source=EntitySource.CAPTION,
                    context="Great restaurant"
                )
            ],
            topics=['food'],
            keywords=['great', 'restaurant']
        )
        
        # Mock hashtag analysis
        mock_analyze_hashtags.return_value = {
            'categories': {'food': ['food', 'restaurant']},
            'topics': ['food'],
            'entities': [
                Entity(
                    name="Food",
                    category=EntityCategory.CONCEPT,
                    confidence=0.8,
                    source=EntitySource.HASHTAG,
                    context="#food"
                )
            ]
        }
        
        caption = "Great restaurant! #food #restaurant"
        result = self.processor.process_text_content(caption)
        
        assert isinstance(result, TextAnalysis)
        assert len(result.extracted_entities) == 2  # Combined from both analyses
        assert 'food' in result.topics
        assert len(result.keywords) == 2
    
    @patch('src.analysis.text_processor.TextProcessor.extract_hashtags')
    @patch('src.analysis.text_processor.TextProcessor.analyze_caption')
    @patch('src.analysis.text_processor.TextProcessor.analyze_hashtags')
    def test_process_text_content_with_hashtag_extraction(self, mock_analyze_hashtags, mock_analyze_caption, mock_extract_hashtags):
        """Test text processing when hashtags need to be extracted."""
        # Mock hashtag extraction
        mock_extract_hashtags.return_value = ['food', 'restaurant']
        
        # Mock analyses
        mock_analyze_caption.return_value = TextAnalysis(
            content_id="",
            extracted_entities=[],
            topics=[],
            keywords=[]
        )
        
        mock_analyze_hashtags.return_value = {
            'categories': {},
            'topics': [],
            'entities': []
        }
        
        caption = "Great food! #food #restaurant"
        result = self.processor.process_text_content(caption, hashtags=None)
        
        # Should call extract_hashtags when hashtags not provided
        mock_extract_hashtags.assert_called_once_with(caption)
        assert isinstance(result, TextAnalysis)
    
    def test_parse_gpt_entity_response_valid_json(self):
        """Test parsing valid JSON response from GPT."""
        response_text = '''[
            {
                "name": "Starbucks",
                "category": "BRAND",
                "confidence": 0.9,
                "context": "Coffee at Starbucks"
            }
        ]'''
        
        entities = self.processor._parse_gpt_entity_response(
            response_text, EntitySource.CAPTION, "Coffee at Starbucks"
        )
        
        assert len(entities) == 1
        assert entities[0].name == "Starbucks"
        assert entities[0].category == EntityCategory.BRAND
        assert entities[0].confidence == 0.9
    
    def test_parse_gpt_entity_response_invalid_json(self):
        """Test parsing invalid JSON response from GPT."""
        response_text = "This is not valid JSON"
        
        entities = self.processor._parse_gpt_entity_response(
            response_text, EntitySource.CAPTION, "Test text"
        )
        
        # Should handle gracefully and return empty list or fallback results
        assert isinstance(entities, list)
    
    def test_parse_gpt_entity_response_low_confidence(self):
        """Test filtering out low confidence entities."""
        response_text = '''[
            {
                "name": "Low Confidence Entity",
                "category": "PRODUCT",
                "confidence": 0.3,
                "context": "Test"
            },
            {
                "name": "High Confidence Entity",
                "category": "PRODUCT",
                "confidence": 0.8,
                "context": "Test"
            }
        ]'''
        
        entities = self.processor._parse_gpt_entity_response(
            response_text, EntitySource.CAPTION, "Test text"
        )
        
        # Should only include high confidence entity
        assert len(entities) == 1
        assert entities[0].name == "High Confidence Entity"
    
    def test_fallback_entity_extraction(self):
        """Test fallback entity extraction when JSON parsing fails."""
        response_text = """
        Product: iPhone (0.9)
        Location: New York (0.8)
        Brand: Apple (0.7)
        """
        
        entities = self.processor._fallback_entity_extraction(
            response_text, EntitySource.CAPTION, "Test text"
        )
        
        # Should extract entities using pattern matching
        assert len(entities) >= 1
        # Check that at least one entity was extracted
        entity_names = [e.name for e in entities]
        assert any(name in ['iPhone', 'New York', 'Apple'] for name in entity_names)