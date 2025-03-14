"""
Utility functions for webpage monitoring
"""
import hashlib
import logging
import time
from typing import Optional, Tuple
from datetime import datetime
from difflib import unified_diff

def setup_logging() -> None:
    """Configure logging with timestamp and appropriate format"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 hash of content for efficient comparison"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def format_timestamp() -> str:
    """Return formatted current timestamp"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def exponential_backoff(attempt: int, base_delay: int, max_delay: int) -> int:
    """Calculate exponential backoff delay"""
    delay = min(base_delay * (2 ** attempt), max_delay)
    return delay

def extract_relevant_content(soup) -> Tuple[str, Optional[str]]:
    """
    Extract relevant content from BeautifulSoup object
    Returns tuple of (content, selector_used)
    """
    # Try different common selectors for main content
    selectors = [
        ('main', 'main'),
        ('#content', '#content'),
        ('.content', '.content'),
        ('article', 'article'),
        ('body', 'body')
    ]

    for selector, selector_name in selectors:
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True), selector_name

    # Fallback to body if no specific content area found
    return soup.body.get_text(strip=True), 'body'

def get_content_diff(old_content: str, new_content: str) -> str:
    """
    Generate a human-readable diff between old and new content
    """
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    diff = list(unified_diff(
        old_lines,
        new_lines,
        fromfile='previous',
        tofile='current',
        lineterm='',
        n=3  # Context lines
    ))

    if diff:
        return '\n'.join(diff)
    return "コンテンツは変更されましたが、差分を特定できませんでした。"