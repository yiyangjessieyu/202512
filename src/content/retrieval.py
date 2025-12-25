"""
Content Retrieval Engine for collecting saved Instagram content.
"""

import time
import random
import logging
import os
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from src.models.content import (
    ContentItem, MediaFile, ContentMetadata, ContentType, 
    MediaType, EngagementData
)

logger = logging.getLogger(__name__)


class ContentRetrievalEngine:
    """Orchestrates browser automation to collect saved Instagram content."""
    
    def __init__(self, headless: bool = True, download_dir: str = "temp"):
        """
        Initialize the content retrieval engine.
        
        Args:
            headless: Whether to run browser in headless mode
            download_dir: Directory for downloading media files
        """
        self.headless = headless
        self.download_dir = download_dir
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.rate_limit_delay = 1.0  # Base delay between requests
        self.max_retries = 3
        
        # Create download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Add options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent to appear more human-like
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Set download preferences
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _human_like_delay(self, min_delay: float = 1.0, max_delay: float = 3.0) -> None:
        """Add human-like delay between actions."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _scroll_to_load_content(self, max_scrolls: int = 10) -> None:
        """Scroll down to load more content with Instagram's infinite scroll."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls = 0
        
        while scrolls < max_scrolls:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            self._human_like_delay(2.0, 4.0)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                # No new content loaded, try a few more times
                if scrolls >= 3:
                    break
            
            last_height = new_height
            scrolls += 1
            
            logger.info(f"Scrolled {scrolls} times, page height: {new_height}")
    
    def collect_saved_content(self, session_id: str) -> List[ContentItem]:
        """
        Retrieves all saved posts and reels from Instagram saved collection.
        
        Args:
            session_id: User session identifier (not used in browser automation)
            
        Returns:
            List of collected content items
        """
        content_items = []
        
        try:
            # Set up browser driver
            self.driver = self._setup_driver()
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info("Navigating to Instagram saved collection")
            
            # Navigate to Instagram saved collection
            # Note: User must be logged in already or this will fail
            self.driver.get("https://www.instagram.com/accounts/login/")
            self._human_like_delay(3.0, 5.0)
            
            # Check if already logged in by looking for saved collection link
            try:
                # Try to navigate directly to saved collection
                self.driver.get("https://www.instagram.com/username/saved/")  # This will redirect if not logged in
                self._human_like_delay(2.0, 4.0)
                
                # Check if we're on login page (indicates not logged in)
                if "login" in self.driver.current_url:
                    logger.error("User not logged in. Please log in to Instagram first.")
                    return content_items
                
            except Exception as e:
                logger.error(f"Error accessing saved collection: {e}")
                return content_items
            
            # Scroll to load all saved content
            logger.info("Loading saved content...")
            self._scroll_to_load_content(max_scrolls=20)
            
            # Find all saved content items
            content_elements = self.driver.find_elements(By.CSS_SELECTOR, "article a[href*='/p/'], article a[href*='/reel/']")
            
            logger.info(f"Found {len(content_elements)} saved content items")
            
            for idx, element in enumerate(content_elements):
                try:
                    # Extract basic information from the element
                    content_url = element.get_attribute("href")
                    if not content_url:
                        continue
                    
                    # Determine content type from URL
                    content_type = ContentType.REEL if "/reel/" in content_url else ContentType.POST
                    
                    # Extract content ID from URL
                    content_id = self._extract_content_id(content_url)
                    if not content_id:
                        continue
                    
                    # Create basic content item (metadata will be extracted separately)
                    content_item = ContentItem(
                        id=content_id,
                        url=content_url,
                        content_type=content_type,
                        timestamp=datetime.utcnow(),  # Will be updated with actual timestamp
                        author="",  # Will be extracted in metadata extraction
                        caption="",  # Will be extracted in metadata extraction
                        hashtags=[],  # Will be extracted in metadata extraction
                        media_files=[],  # Will be populated in media download
                        engagement_metrics=EngagementData()  # Will be extracted in metadata extraction
                    )
                    
                    content_items.append(content_item)
                    
                    # Add delay to avoid being detected as bot
                    if idx % 10 == 0:  # Every 10 items
                        self._human_like_delay(2.0, 4.0)
                        
                except Exception as e:
                    logger.warning(f"Error processing content element {idx}: {e}")
                    continue
            
            logger.info(f"Successfully collected {len(content_items)} content items")
            
        except Exception as e:
            logger.error(f"Error during content collection: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
        
        return content_items
    
    def _extract_content_id(self, url: str) -> Optional[str]:
        """Extract Instagram content ID from URL."""
        # Instagram URLs format: https://www.instagram.com/p/CONTENT_ID/ or /reel/CONTENT_ID/
        match = re.search(r'/(p|reel)/([A-Za-z0-9_-]+)/', url)
        return match.group(2) if match else None
    
    def download_media(self, content_url: str) -> MediaFile:
        """
        Downloads video/audio files for processing.
        
        Args:
            content_url: URL of media to download
            
        Returns:
            Downloaded media file information
        """
        try:
            # Set up driver if not already done
            if not self.driver:
                self.driver = self._setup_driver()
                self.wait = WebDriverWait(self.driver, 10)
            
            logger.info(f"Downloading media from: {content_url}")
            
            # Navigate to the content page
            self.driver.get(content_url)
            self._human_like_delay(2.0, 4.0)
            
            # Try to find video element first (for reels and video posts)
            video_elements = self.driver.find_elements(By.TAG_NAME, "video")
            
            if video_elements:
                # Handle video content
                video_element = video_elements[0]
                video_src = video_element.get_attribute("src")
                
                if video_src:
                    media_file = self._download_file(video_src, MediaType.VIDEO)
                    
                    # Extract additional video metadata
                    try:
                        duration = video_element.get_attribute("duration")
                        if duration:
                            media_file.duration = float(duration)
                    except (ValueError, TypeError):
                        pass
                    
                    return media_file
            
            # If no video, look for carousel or multiple images
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, "article img[src*='instagram']")
            
            if img_elements:
                # For carousel posts, download the first image
                # TODO: In future, could download all carousel images
                img_element = img_elements[0]
                img_src = img_element.get_attribute("src")
                
                if img_src:
                    media_file = self._download_file(img_src, MediaType.IMAGE)
                    
                    # Extract image dimensions if available
                    try:
                        width = img_element.get_attribute("width")
                        height = img_element.get_attribute("height")
                        if width and height:
                            media_file.resolution = (int(width), int(height))
                    except (ValueError, TypeError):
                        pass
                    
                    return media_file
            
            raise Exception("No media found in content")
            
        except Exception as e:
            logger.error(f"Error downloading media from {content_url}: {e}")
            raise
    
    def _download_file(self, url: str, media_type: MediaType) -> MediaFile:
        """Download file from URL and return MediaFile object."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Generate filename
            content_id = str(int(time.time() * 1000))  # Use timestamp as unique ID
            extension = ".mp4" if media_type == MediaType.VIDEO else ".jpg"
            filename = f"{content_id}{extension}"
            file_path = os.path.join(self.download_dir, filename)
            
            # Download file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create MediaFile object
            media_file = MediaFile(
                file_path=file_path,
                media_type=media_type,
                duration=None,  # Will be determined by analysis pipeline
                resolution=None,  # Will be determined by analysis pipeline
                file_size=file_size
            )
            
            logger.info(f"Downloaded {media_type.value} file: {file_path} ({file_size} bytes)")
            return media_file
            
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")
            raise
    
    def extract_metadata(self, content_item: ContentItem) -> ContentMetadata:
        """
        Collects captions, hashtags, and engagement data from content page.
        
        Args:
            content_item: Content item to extract metadata from
            
        Returns:
            Extracted metadata
        """
        try:
            # Set up driver if not already done
            if not self.driver:
                self.driver = self._setup_driver()
                self.wait = WebDriverWait(self.driver, 10)
            
            logger.info(f"Extracting metadata from: {content_item.url}")
            
            # Navigate to content page
            self.driver.get(content_item.url)
            self._human_like_delay(2.0, 4.0)
            
            extracted_text = []
            
            # Extract caption text
            try:
                # Look for caption in various possible selectors
                caption_selectors = [
                    "article div[data-testid='post-caption'] span",
                    "article h1",
                    "div[role='button'] span",
                    "article span[dir='auto']",
                    "div[data-testid='post-caption']",
                    "article div span:not([aria-label])"
                ]
                
                caption_text = ""
                for selector in caption_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Filter out short non-caption text
                            caption_text = text
                            break
                    if caption_text:
                        break
                
                if caption_text:
                    extracted_text.append(caption_text)
                    # Update the content item with extracted caption
                    content_item.caption = caption_text
                    
                    # Extract hashtags from caption
                    hashtags = re.findall(r'#\w+', caption_text)
                    content_item.hashtags = [tag.lower() for tag in hashtags]
                    
                    # Extract mentions from caption
                    mentions = re.findall(r'@\w+', caption_text)
                    if mentions:
                        extracted_text.extend(mentions)
                
            except Exception as e:
                logger.warning(f"Error extracting caption: {e}")
            
            # Extract author information
            try:
                author_selectors = [
                    "article header a[role='link']",
                    "header a span",
                    "article header span[dir='auto']"
                ]
                
                for selector in author_selectors:
                    author_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if author_elements:
                        author_text = author_elements[0].text.strip()
                        if author_text and not author_text.startswith('#'):
                            content_item.author = author_text
                            break
                            
            except Exception as e:
                logger.warning(f"Error extracting author: {e}")
            
            # Extract engagement metrics (likes, comments, views)
            try:
                # Look for like count
                engagement_selectors = [
                    "section button span[dir='auto']",
                    "section span[dir='auto']",
                    "article section div span"
                ]
                
                for selector in engagement_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip().lower()
                        
                        # Extract likes
                        if "like" in text and not content_item.engagement_metrics.likes:
                            numbers = re.findall(r'[\d,]+', text)
                            if numbers:
                                try:
                                    likes = int(numbers[0].replace(',', ''))
                                    content_item.engagement_metrics.likes = likes
                                except ValueError:
                                    pass
                        
                        # Extract comments
                        elif "comment" in text and not content_item.engagement_metrics.comments:
                            numbers = re.findall(r'[\d,]+', text)
                            if numbers:
                                try:
                                    comments = int(numbers[0].replace(',', ''))
                                    content_item.engagement_metrics.comments = comments
                                except ValueError:
                                    pass
                        
                        # Extract views (for videos)
                        elif "view" in text and not content_item.engagement_metrics.views:
                            numbers = re.findall(r'[\d,]+', text)
                            if numbers:
                                try:
                                    views = int(numbers[0].replace(',', ''))
                                    content_item.engagement_metrics.views = views
                                except ValueError:
                                    pass
                        
            except Exception as e:
                logger.warning(f"Error extracting engagement metrics: {e}")
            
            # Extract timestamp
            try:
                time_elements = self.driver.find_elements(By.CSS_SELECTOR, "time[datetime]")
                if time_elements:
                    datetime_str = time_elements[0].get_attribute("datetime")
                    if datetime_str:
                        # Handle different datetime formats
                        try:
                            content_item.timestamp = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                        except ValueError:
                            # Try alternative parsing
                            content_item.timestamp = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                            
            except Exception as e:
                logger.warning(f"Error extracting timestamp: {e}")
            
            # Extract location information if available
            try:
                location_elements = self.driver.find_elements(By.CSS_SELECTOR, "article header div a[href*='/explore/locations/']")
                if location_elements:
                    location_text = location_elements[0].text.strip()
                    if location_text:
                        extracted_text.append(f"Location: {location_text}")
                        
            except Exception as e:
                logger.warning(f"Error extracting location: {e}")
            
            # Extract alt text from images (accessibility text often contains useful descriptions)
            try:
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, "article img[alt]")
                for img in img_elements:
                    alt_text = img.get_attribute("alt")
                    if alt_text and alt_text.strip() and "photo by" not in alt_text.lower():
                        extracted_text.append(f"Image description: {alt_text.strip()}")
                        
            except Exception as e:
                logger.warning(f"Error extracting alt text: {e}")
            
            # Create metadata object
            metadata = ContentMetadata(
                content_id=content_item.id,
                extracted_text=extracted_text,
                detected_objects=[],  # Will be populated by vision analysis
                audio_features=None,  # Will be populated by audio analysis
                processing_timestamp=datetime.utcnow()
            )
            
            logger.info(f"Successfully extracted metadata for content {content_item.id}")
            logger.debug(f"Extracted text: {extracted_text}")
            logger.debug(f"Author: {content_item.author}")
            logger.debug(f"Hashtags: {content_item.hashtags}")
            logger.debug(f"Engagement: {content_item.engagement_metrics}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {content_item.url}: {e}")
            raise
    
    def handle_rate_limits(self) -> None:
        """Handle Instagram rate limits with exponential backoff."""
        logger.warning("Rate limit detected, implementing backoff strategy")
        
        # Exponential backoff: start with base delay and double it
        self.rate_limit_delay = min(self.rate_limit_delay * 2, 60.0)  # Cap at 60 seconds
        
        logger.info(f"Waiting {self.rate_limit_delay} seconds before retry")
        time.sleep(self.rate_limit_delay)
    
    def process_content_batch(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """
        Process a batch of content items to download media and extract metadata.
        
        Args:
            content_items: List of content items to process
            
        Returns:
            List of processed content items with media and metadata
        """
        processed_items = []
        
        try:
            # Set up driver once for the entire batch
            self.driver = self._setup_driver()
            self.wait = WebDriverWait(self.driver, 10)
            
            for idx, content_item in enumerate(content_items):
                try:
                    logger.info(f"Processing content item {idx + 1}/{len(content_items)}: {content_item.id}")
                    
                    # Extract metadata first (this updates the content_item in place)
                    metadata = self.extract_metadata(content_item)
                    
                    # Download media file
                    try:
                        media_file = self.download_media(content_item.url)
                        content_item.media_files = [media_file]
                    except Exception as e:
                        logger.warning(f"Failed to download media for {content_item.id}: {e}")
                        # Continue processing even if media download fails
                    
                    processed_items.append(content_item)
                    
                    # Add delay between items to avoid rate limiting
                    if idx < len(content_items) - 1:  # Don't delay after the last item
                        self._human_like_delay(3.0, 6.0)
                    
                except Exception as e:
                    logger.error(f"Error processing content item {content_item.id}: {e}")
                    # Add the item even if processing failed partially
                    processed_items.append(content_item)
                    
                    # Check if we hit rate limits
                    if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                        self.handle_rate_limits()
                    
        except Exception as e:
            logger.error(f"Error during batch processing: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
        
        logger.info(f"Batch processing complete. Processed {len(processed_items)}/{len(content_items)} items")
        return processed_items

    def __del__(self):
        """Cleanup driver on object destruction."""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass