"""
Example usage of ContentRetrievalEngine.

This example demonstrates how to use the ContentRetrievalEngine to collect
and process Instagram saved content.
"""

import logging
from src.content.retrieval import ContentRetrievalEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Example of using ContentRetrievalEngine."""
    
    # Initialize the content retrieval engine
    engine = ContentRetrievalEngine(
        headless=False,  # Set to True for production
        download_dir="temp/downloads"
    )
    
    try:
        # Step 1: Collect saved content
        logger.info("Collecting saved content from Instagram...")
        content_items = engine.collect_saved_content(session_id="example_session")
        
        logger.info(f"Found {len(content_items)} saved content items")
        
        # Step 2: Process content items (download media and extract metadata)
        if content_items:
            logger.info("Processing content items...")
            processed_items = engine.process_content_batch(content_items[:5])  # Process first 5 items
            
            # Display results
            for item in processed_items:
                logger.info(f"Processed item {item.id}:")
                logger.info(f"  - Author: {item.author}")
                logger.info(f"  - Caption: {item.caption[:100]}..." if len(item.caption) > 100 else f"  - Caption: {item.caption}")
                logger.info(f"  - Hashtags: {item.hashtags}")
                logger.info(f"  - Likes: {item.engagement_metrics.likes}")
                logger.info(f"  - Comments: {item.engagement_metrics.comments}")
                logger.info(f"  - Media files: {len(item.media_files)}")
                logger.info("---")
        
    except Exception as e:
        logger.error(f"Error during content retrieval: {e}")
    
    logger.info("Content retrieval example completed")


if __name__ == "__main__":
    main()