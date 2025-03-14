"""
Configuration settings for the webpage monitor
"""
import os
import argparse

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='ウェブページの変更を監視するスクリプト')
    parser.add_argument('--url', help='監視するウェブページのURL', default=os.getenv('MONITOR_URL'))
    parser.add_argument('--interval', type=int, help='チェック間隔（秒）', default=int(os.getenv('MONITOR_INTERVAL', '60')))
    parser.add_argument('--test', action='store_true', help='テストモードで実行（コンテンツの変更をシミュレート）')
    return parser.parse_args()

# Default URL to monitor if not specified
DEFAULT_URL = "https://example.com"

# Default monitoring interval in seconds
DEFAULT_INTERVAL = 60

# Maximum retry attempts for failed requests
MAX_RETRIES = 3

# Base delay for exponential backoff (in seconds)
BACKOFF_DELAY = 5

# Maximum delay between retries (in seconds)
MAX_DELAY = 300

# User agent string to identify the script
USER_AGENT = "WebpageMonitor/1.0"

# Logging format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Get configuration from arguments or environment variables with defaults
args = parse_arguments()
URL = args.url or DEFAULT_URL
INTERVAL = args.interval or DEFAULT_INTERVAL
TEST_MODE = args.test