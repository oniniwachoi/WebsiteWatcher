"""
Main script for monitoring webpage changes
"""
import time
import logging
import requests
import argparse
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import trafilatura

from config import DEFAULT_CONFIG, HEADERS, MAX_RETRIES, RETRY_DELAY, REQUEST_TIMEOUT
from utils import setup_logging, is_valid_url, calculate_content_hash, extract_relevant_content

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Monitor webpage for changes')
    parser.add_argument('--url', type=str, default='https://example.com',
                      help='URL to monitor')
    parser.add_argument('--interval', type=int, default=DEFAULT_CONFIG['INTERVAL'],
                      help='Monitoring interval in seconds')
    parser.add_argument('--selector', type=str,
                      help='CSS selector to monitor specific element')
    parser.add_argument('--use-trafilatura', action='store_true',
                      help='Use trafilatura for content extraction')
    return parser.parse_args()

class WebpageMonitor:
    def __init__(
        self,
        url: str,
        interval: int = DEFAULT_CONFIG['INTERVAL'],
        selector: Optional[str] = None,
        use_trafilatura: bool = False
    ):
        """
        Initialize webpage monitor

        Args:
            url: URL to monitor
            interval: Monitoring interval in seconds
            selector: CSS selector to monitor specific element
            use_trafilatura: Whether to use trafilatura for content extraction
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL provided: {url}")

        self.url = url
        self.interval = interval
        self.selector = selector
        self.use_trafilatura = use_trafilatura
        self.previous_hash = None
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        setup_logging()
        self.logger = logging.getLogger(__name__)

    def get_page_content(self) -> Optional[str]:
        """
        Fetch webpage content with retry mechanism

        Returns:
            Optional[str]: Page content or None if failed
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    self.url,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()

                if self.use_trafilatura:
                    return trafilatura.extract(response.text)

                soup = BeautifulSoup(response.text, 'html.parser')
                return extract_relevant_content(soup, self.selector)

            except requests.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.logger.error(f"Failed to fetch {self.url} after {MAX_RETRIES} attempts")
                    return None

    def check_for_changes(self) -> Dict[str, Any]:
        """
        Check for changes in webpage content

        Returns:
            Dict containing status and change information
        """
        content = self.get_page_content()
        if content is None:
            return {'status': 'error', 'message': 'Failed to fetch content'}

        current_hash = calculate_content_hash(content)

        if self.previous_hash is None:
            self.previous_hash = current_hash
            return {
                'status': 'initial',
                'message': 'Initial content captured',
                'content': content
            }

        if current_hash != self.previous_hash:
            self.previous_hash = current_hash
            return {
                'status': 'changed',
                'message': 'Content changed',
                'content': content
            }

        return {
            'status': 'unchanged',
            'message': 'No changes detected'
        }

    def start_monitoring(self):
        """Start the monitoring loop"""
        self.logger.info(f"Starting to monitor {self.url}")
        self.logger.info(f"Checking every {self.interval} seconds")

        try:
            while True:
                result = self.check_for_changes()

                if result['status'] == 'error':
                    self.logger.error(result['message'])
                elif result['status'] == 'changed':
                    self.logger.info("Change detected!")
                    self.logger.info(f"New content: {result['content'][:200]}...")
                elif result['status'] == 'initial':
                    self.logger.info("Initial content captured")
                else:
                    self.logger.info("No changes detected")

                time.sleep(self.interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
        finally:
            self.session.close()

if __name__ == "__main__":
    args = parse_arguments()
    monitor = WebpageMonitor(
        url=args.url,
        interval=args.interval,
        selector=args.selector,
        use_trafilatura=args.use_trafilatura
    )
    monitor.start_monitoring()