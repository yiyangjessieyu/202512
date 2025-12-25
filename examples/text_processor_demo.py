#!/usr/bin/env python3
"""
Demo script for TextProcessor functionality.

This script demonstrates the TextProcessor capabilities without requiring OpenAI API calls.
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.analysis.text_processor import TextProcessor


def demo_text_processor():
    """Demonstrate TextProcessor functionality."""
    print("=== TextProcessor Demo ===\n")
    
    processor = TextProcessor()
    
    # Test caption
    caption = """Amazing dinner at Pizza Palace! The food was incredible and the service was outstanding. 
    Highly recommend the margherita pizza and tiramisu. Perfect date night spot! 
    #food #restaurant #italian #pizza #datenight #delicious #foodie #yummy"""
    
    print(f"Sample Caption:\n{caption}\n")
    
    # Extract hashtags
    print("1. Hashtag Extraction:")
    hashtags = processor.extract_hashtags(caption)
    print(f"   Found {len(hashtags)} hashtags: {hashtags}\n")
    
    # Categorize hashtags
    print("2. Hashtag Categorization:")
    categories = processor.categorize_hashtags(hashtags)
    for category, tags in categories.items():
        print(f"   {category.title()}: {tags}")
    print()
    
    # Extract keywords
    print("3. Keyword Extraction:")
    caption_text = caption.split('#')[0]  # Remove hashtags for keyword extraction
    keywords = processor._extract_keywords(caption_text)
    print(f"   Keywords: {keywords}\n")
    
    # Test different types of content
    print("4. Different Content Types:")
    
    test_cases = [
        ("Travel: Exploring the beautiful beaches of Santorini! #travel #greece #vacation #wanderlust", "Travel"),
        ("New workout routine crushing it! 💪 #fitness #gym #workout #health #motivation", "Fitness"),
        ("Latest iPhone review - amazing camera quality! #tech #apple #iphone #review #technology", "Technology"),
        ("Homemade pasta recipe from scratch 🍝 #cooking #recipe #italian #homemade #food", "Cooking")
    ]
    
    for test_caption, content_type in test_cases:
        print(f"   {content_type}:")
        test_hashtags = processor.extract_hashtags(test_caption)
        test_categories = processor.categorize_hashtags(test_hashtags)
        print(f"     Hashtags: {test_hashtags}")
        print(f"     Categories: {list(test_categories.keys())}")
        print()
    
    print("5. Text Analysis (without OpenAI API):")
    # Demonstrate the analyze_caption method structure
    print("   The TextProcessor can analyze captions to extract:")
    print("   - Entities (products, locations, brands, people, concepts)")
    print("   - Topics from hashtag categorization")
    print("   - Keywords from caption text")
    print("   - Content categorization")
    print()
    print("   Note: Entity extraction requires OpenAI API key for full functionality.")
    print("   Hashtag categorization and keyword extraction work offline.")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_text_processor()