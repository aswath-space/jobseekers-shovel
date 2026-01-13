"""
HTTP crawler with respectful crawling practices.

Implements rate limiting, delays, retries, and proper error handling.
"""

import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.utils.logging import get_logger


class CrawlerError(Exception):
    """Raised when crawling fails."""
    pass


class RateLimitedSession:
    """
    HTTP session with rate limiting and respectful crawling practices.

    Features:
    - Configurable delays between requests to same host
    - Custom User-Agent
    - Automatic retries with exponential backoff
    - Timeout handling
    - Per-host request tracking
    """

    def __init__(
        self,
        request_delay: float = 2.0,
        user_agent: str = "JobSeekersShovel/1.0",
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
    ):
        """
        Initialize rate-limited session.

        Args:
            request_delay: Minimum seconds between requests to same host
            user_agent: User-Agent header value
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            retry_backoff: Backoff multiplier for retries
        """
        self.request_delay = request_delay
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.logger = get_logger(__name__)

        # Track last request time per host
        self._last_request_time: Dict[str, float] = {}

        # Create session with retry configuration
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry configuration.

        Returns:
            Configured requests Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

        return session

    def _get_host(self, url: str) -> str:
        """
        Extract host from URL.

        Args:
            url: Full URL

        Returns:
            Host string (e.g., "example.com")
        """
        parsed = urlparse(url)
        return parsed.netloc

    def _wait_for_rate_limit(self, host: str) -> None:
        """
        Wait if necessary to respect rate limit for host.

        Args:
            host: Host to check rate limit for
        """
        if host not in self._last_request_time:
            return

        elapsed = time.time() - self._last_request_time[host]
        if elapsed < self.request_delay:
            wait_time = self.request_delay - elapsed
            self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {host}")
            time.sleep(wait_time)

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Perform GET request with rate limiting.

        Args:
            url: URL to fetch
            **kwargs: Additional arguments to pass to requests.get()

        Returns:
            Response object

        Raises:
            CrawlerError: If request fails after all retries
        """
        host = self._get_host(url)

        # Apply rate limiting
        self._wait_for_rate_limit(host)

        # Set default timeout if not provided
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            self.logger.debug(f"GET {url}")
            response = self.session.get(url, **kwargs)

            # Update last request time
            self._last_request_time[host] = time.time()

            # Raise for HTTP errors
            response.raise_for_status()

            self.logger.debug(
                f"GET {url} -> {response.status_code} ({len(response.content)} bytes)"
            )

            return response

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout after {self.timeout}s: {url}"
            self.logger.error(error_msg)
            raise CrawlerError(error_msg) from e

        except requests.exceptions.TooManyRedirects as e:
            error_msg = f"Too many redirects: {url}"
            self.logger.error(error_msg)
            raise CrawlerError(error_msg) from e

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}: {url}"
            self.logger.error(error_msg)
            raise CrawlerError(error_msg) from e

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {url}"
            self.logger.error(error_msg)
            raise CrawlerError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {url} - {e}"
            self.logger.error(error_msg)
            raise CrawlerError(error_msg) from e

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_crawler_from_config(config: Dict[str, Any]) -> RateLimitedSession:
    """
    Create crawler from configuration dictionary.

    Args:
        config: Configuration dict with crawling settings

    Returns:
        Configured RateLimitedSession
    """
    crawling_config = config.get("crawling", {})

    return RateLimitedSession(
        request_delay=crawling_config.get("request_delay_seconds", 2.0),
        user_agent=crawling_config.get(
            "user_agent", "JobSeekersShovel/1.0 (Personal Job Tracker)"
        ),
        timeout=crawling_config.get("timeout_seconds", 30),
        max_retries=crawling_config.get("max_retries", 3),
        retry_backoff=crawling_config.get("retry_backoff", 1.0),
    )
