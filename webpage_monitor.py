"""
Web Page Monitor - A script to monitor webpage changes
"""
import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, Tuple
import trafilatura

from config import (
    URL, INTERVAL, MAX_RETRIES, BACKOFF_DELAY,
    MAX_DELAY, USER_AGENT
)
from utils import (
    setup_logging,
    calculate_content_hash,
    format_timestamp,
    exponential_backoff,
    extract_relevant_content,
    get_content_diff
)

class WebpageMonitor:
    def __init__(self, url: str, interval: int, test_mode: bool = False):
        self.url = url
        self.interval = interval
        self.last_content: Optional[str] = None
        self.last_content_hash: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.consecutive_errors = 0
        self.test_mode = test_mode
        self.test_counter = 0

    def fetch_content(self) -> Optional[str]:
        """Fetch webpage content with error handling and retries"""
        if self.test_mode:
            # In test mode, simulate content changes
            self.test_counter += 1
            return f"Test content version {self.test_counter}"

        logging.debug(f"URLからコンテンツを取得しています: {self.url}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(self.url, timeout=30)
                response.raise_for_status()
                logging.debug(f"ステータスコード: {response.status_code}")

                # Try trafilatura first for better content extraction
                downloaded = trafilatura.fetch_url(self.url)
                if downloaded:
                    content = trafilatura.extract(downloaded)
                    if content:
                        logging.debug("Trafilaturaを使用してコンテンツを抽出しました")
                        return content

                # Fallback to BeautifulSoup if trafilatura fails
                logging.debug("BeautifulSoupにフォールバックします")
                soup = BeautifulSoup(response.text, 'html.parser')
                content, selector = extract_relevant_content(soup)
                logging.debug(f"セレクター {selector} を使用してコンテンツを抽出しました")
                return content

            except requests.RequestException as e:
                delay = exponential_backoff(attempt, BACKOFF_DELAY, MAX_DELAY)
                logging.error(f"リクエストに失敗しました (試行 {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                logging.info(f"{delay}秒後に再試行します...")
                time.sleep(delay)

        self.consecutive_errors += 1
        return None

    def check_for_changes(self) -> None:
        """Check for changes in webpage content"""
        content = self.fetch_content()

        if content is None:
            logging.error("コンテンツの取得に失敗しました")
            return

        current_hash = calculate_content_hash(content)
        logging.debug(f"現在のコンテンツハッシュ: {current_hash[:8]}...")

        if self.last_content_hash is None:
            logging.info("初期コンテンツのスナップショットを作成しました")
            logging.debug(f"コンテンツの長さ: {len(content)} 文字")
            self.last_content = content
            self.last_content_hash = current_hash
        elif current_hash != self.last_content_hash:
            logging.info("変更を検出しました！")
            logging.info(f"タイムスタンプ: {format_timestamp()}")
            logging.debug(f"前回のハッシュ: {self.last_content_hash[:8]}...")
            logging.debug(f"現在のハッシュ: {current_hash[:8]}...")

            # Generate and log the diff
            if self.last_content:
                diff = get_content_diff(self.last_content, content)
                logging.info("変更の詳細:")
                logging.info(diff)

            self.last_content = content
            self.last_content_hash = current_hash
            self.consecutive_errors = 0
        else:
            logging.info("変更は検出されませんでした")
            self.consecutive_errors = 0

    def run(self) -> None:
        """Main monitoring loop"""
        logging.info(f"{self.url} の監視を開始します")
        logging.info(f"{self.interval}秒ごとにチェックします")
        if self.test_mode:
            logging.info("テストモードで実行中")

        while True:
            try:
                self.check_for_changes()

                # Implement increasing intervals if too many errors
                if self.consecutive_errors > MAX_RETRIES:
                    adjusted_interval = min(self.interval * 2, MAX_DELAY)
                    logging.warning(f"エラーが多すぎるため、間隔を{adjusted_interval}秒に増やします")
                    time.sleep(adjusted_interval)
                else:
                    time.sleep(self.interval)

            except KeyboardInterrupt:
                logging.info("ユーザーによって監視が停止されました")
                break
            except Exception as e:
                logging.error(f"予期せぬエラー: {str(e)}")
                time.sleep(self.interval)

def main():
    """Main entry point"""
    setup_logging()
    # Set debug level for more detailed logging
    logging.getLogger().setLevel(logging.DEBUG)
    monitor = WebpageMonitor(URL, INTERVAL)
    monitor.run()

if __name__ == "__main__":
    main()