"""
Configuration settings for the webpage monitor
"""
import os

# Default configuration
DEFAULT_CONFIG = {
    'INTERVAL': 60,  # Default monitoring interval in seconds
    'USER_AGENT': 'Custom Web Monitor Bot/1.0',  # Identify our bot
    'LOG_FORMAT': '%(asctime)s - %(levelname)s - %(message)s',
    'DATE_FORMAT': '%Y-%m-%d %H:%M:%S'
}

# Maximum number of retries for failed requests
MAX_RETRIES = 3

# Delay between retries (in seconds)
RETRY_DELAY = 5

# Timeout for requests (in seconds)
REQUEST_TIMEOUT = 10

# Headers for requests
HEADERS = {
    'User-Agent': DEFAULT_CONFIG['USER_AGENT'],
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
}
