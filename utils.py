"""
Utility functions for webpage monitoring
"""
import hashlib
import logging
from typing import Optional
from urllib.parse import urlparse

def setup_logging() -> None:
    """Configure logging with proper format"""
    from config import DEFAULT_CONFIG
    
    logging.basicConfig(
        level=logging.INFO,
        format=DEFAULT_CONFIG['LOG_FORMAT'],
        datefmt=DEFAULT_CONFIG['DATE_FORMAT']
    )

def is_valid_url(url: str) -> bool:
    """
    Validate if the given URL is properly formatted
    
    Args:
        url: URL string to validate
    
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def calculate_content_hash(content: str) -> str:
    """
    Calculate SHA-256 hash of content for change detection
    
    Args:
        content: String content to hash
    
    Returns:
        str: Hexadecimal hash of the content
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_relevant_content(soup, selector: Optional[str] = None) -> str:
    """
    Extract content from BeautifulSoup object based on selector
    
    Args:
        soup: BeautifulSoup object
        selector: CSS selector to find specific element (optional)
    
    Returns:
        str: Extracted content
    """
    if selector:
        element = soup.select_one(selector)
        return element.get_text(strip=True) if element else ""
    
    # If no selector provided, get main content
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    return soup.get_text(strip=True)
