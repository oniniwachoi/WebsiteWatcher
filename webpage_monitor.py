"""
Main script for monitoring webpage changes
"""
import time
import logging
import requests
import argparse
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, Tuple
import trafilatura
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import io
import base64

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
    parser.add_argument('--gui', action='store_true',
                      help='Launch with GUI interface')
    return parser.parse_args()

class WebpageMonitor:
    def __init__(
        self,
        url: str,
        interval: int = DEFAULT_CONFIG['INTERVAL'],
        selector: Optional[str] = None,
        use_trafilatura: bool = False,
        capture_screenshot: bool = True,
        capture_html: bool = True
    ):
        """
        Initialize webpage monitor
        """
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL provided: {url}")

        self.url = url
        self.interval = interval
        self.selector = selector
        self.use_trafilatura = use_trafilatura
        self.capture_screenshot = capture_screenshot
        self.capture_html = capture_html
        self.previous_hash = None
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        # Setup Selenium only if screenshot capture is enabled
        self.driver = None
        if self.capture_screenshot:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=chrome_options)

        setup_logging()
        self.logger = logging.getLogger(__name__)

    def capture_screenshot(self) -> Optional[str]:
        """
        Capture webpage screenshot using Selenium
        Returns base64 encoded PNG image
        """
        if not self.capture_screenshot or not self.driver:
            return None

        try:
            self.driver.get(self.url)
            time.sleep(2)  # Wait for page to load
            screenshot = self.driver.get_screenshot_as_png()
            # Convert to base64 for easy transfer
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {str(e)}")
            return None

    def get_page_content(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetch webpage content with retry mechanism
        Returns (content, screenshot_base64, html_content)
        """
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    self.url,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                response.raise_for_status()

                content = None
                if self.use_trafilatura:
                    content = trafilatura.extract(response.text)
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = extract_relevant_content(soup, self.selector)

                screenshot = self.capture_screenshot() if self.capture_screenshot else None
                html = response.text if self.capture_html else None
                return content, screenshot, html

            except requests.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.logger.error(f"Failed to fetch {self.url} after {MAX_RETRIES} attempts")
                    return None, None, None

    def check_for_changes(self) -> Dict[str, Any]:
        """
        Check for changes in webpage content
        """
        content, screenshot, html = self.get_page_content()
        if content is None:
            return {
                'status': 'error',
                'message': 'Failed to fetch content',
                'screenshot': None,
                'html': None
            }

        current_hash = calculate_content_hash(content)

        if self.previous_hash is None:
            self.previous_hash = current_hash
            return {
                'status': 'initial',
                'message': 'Initial content captured',
                'content': content,
                'screenshot': screenshot,
                'html': html
            }

        if current_hash != self.previous_hash:
            self.previous_hash = current_hash
            return {
                'status': 'changed',
                'message': 'Content changed',
                'content': content,
                'screenshot': screenshot,
                'html': html
            }

        return {
            'status': 'unchanged',
            'message': 'No changes detected',
            'screenshot': screenshot,
            'html': html
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
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    args = parse_arguments()
    if args.gui:
        from gui import main
        main()
    else:
        monitor = WebpageMonitor(
            url=args.url,
            interval=args.interval,
            selector=args.selector,
            use_trafilatura=args.use_trafilatura
        )
        monitor.start_monitoring()