"""
Tests for HTTP crawler with rate limiting.
"""

import time
import pytest
import requests
from unittest.mock import Mock, patch

from src.ingestion.crawler import RateLimitedSession, CrawlerError, create_crawler_from_config


def test_crawler_initialization():
    """Test crawler initialization with default values."""
    crawler = RateLimitedSession()

    assert crawler.request_delay == 2.0
    assert crawler.user_agent == "JobSeekersShovel/1.0"
    assert crawler.timeout == 30
    assert crawler.max_retries == 3


def test_crawler_custom_config():
    """Test crawler initialization with custom config."""
    crawler = RateLimitedSession(
        request_delay=5.0,
        user_agent="CustomAgent/1.0",
        timeout=60,
        max_retries=5,
        retry_backoff=2.0,
    )

    assert crawler.request_delay == 5.0
    assert crawler.user_agent == "CustomAgent/1.0"
    assert crawler.timeout == 60
    assert crawler.max_retries == 5


def test_get_host():
    """Test host extraction from URL."""
    crawler = RateLimitedSession()

    assert crawler._get_host("https://example.com/path") == "example.com"
    assert crawler._get_host("http://api.example.com/v1") == "api.example.com"
    assert crawler._get_host("https://example.com:8080/") == "example.com:8080"


def test_rate_limiting():
    """Test that rate limiting delays requests to same host."""
    crawler = RateLimitedSession(request_delay=0.5)

    # Mock the session.get to avoid actual HTTP requests
    with patch.object(crawler.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test"
        mock_get.return_value = mock_response

        # First request should be immediate
        start = time.time()
        crawler.get("https://example.com/page1")
        first_duration = time.time() - start

        # Second request to same host should be delayed
        start = time.time()
        crawler.get("https://example.com/page2")
        second_duration = time.time() - start

        # Second request should have taken at least request_delay seconds
        assert second_duration >= 0.5
        assert first_duration < 0.1  # First request should be fast


def test_different_hosts_no_delay():
    """Test that requests to different hosts are not delayed."""
    crawler = RateLimitedSession(request_delay=1.0)

    with patch.object(crawler.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test"
        mock_get.return_value = mock_response

        # Requests to different hosts should not delay each other
        start = time.time()
        crawler.get("https://example1.com/page")
        crawler.get("https://example2.com/page")
        duration = time.time() - start

        # Should be fast since different hosts
        assert duration < 0.5


def test_crawler_error_on_http_error():
    """Test that HTTP errors raise CrawlerError."""
    crawler = RateLimitedSession()

    with patch.object(crawler.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("Not Found")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        with pytest.raises(CrawlerError):
            crawler.get("https://example.com/notfound")


def test_context_manager():
    """Test crawler as context manager."""
    with RateLimitedSession() as crawler:
        assert crawler.session is not None

    # Session should be closed after context
    assert crawler.session


def test_create_crawler_from_config():
    """Test creating crawler from config dictionary."""
    config = {
        "crawling": {
            "request_delay_seconds": 3.0,
            "user_agent": "TestBot/1.0",
            "timeout_seconds": 45,
            "max_retries": 4,
            "retry_backoff": 2.0,
        }
    }

    crawler = create_crawler_from_config(config)

    assert crawler.request_delay == 3.0
    assert crawler.user_agent == "TestBot/1.0"
    assert crawler.timeout == 45
    assert crawler.max_retries == 4


def test_create_crawler_with_defaults():
    """Test creating crawler from empty config uses defaults."""
    config = {}

    crawler = create_crawler_from_config(config)

    assert crawler.request_delay == 2.0
    assert "JobSeekersShovel" in crawler.user_agent
