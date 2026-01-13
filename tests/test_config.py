"""
Tests for configuration loading and validation.
"""

import pytest
from pathlib import Path

from src.utils.config import Config, ConfigurationError


def test_config_loads_ingestion():
    """Test loading ingestion configuration."""
    config = Config(config_dir="config")
    ingestion = config.load_ingestion_config()

    assert "version" in ingestion
    assert "schedule" in ingestion
    assert "crawling" in ingestion
    assert "classification" in ingestion


def test_config_get_value():
    """Test getting config values with dot notation."""
    config = Config(config_dir="config")

    # Test existing path
    delay = config.get_config_value("crawling.request_delay_seconds")
    assert delay is not None
    assert isinstance(delay, (int, float))

    # Test non-existing path with default
    value = config.get_config_value("nonexistent.path", default=42)
    assert value == 42


def test_config_missing_companies_file():
    """Test error when companies.yml doesn't exist."""
    config = Config(config_dir="nonexistent")

    with pytest.raises(ConfigurationError) as exc_info:
        config.load_companies()

    assert "not found" in str(exc_info.value).lower()


def test_validate_company_entry():
    """Test company entry validation."""
    config = Config()

    # Valid entry
    valid_company = {
        "id": "test-company",
        "name": "Test Company",
        "adapter": "greenhouse",
        "sources": [{"url": "https://example.com"}],
    }
    # Should not raise
    config._validate_company_entry(valid_company, 0)

    # Missing required field
    invalid_company = {
        "id": "test-company",
        "name": "Test Company",
        # Missing adapter and sources
    }
    with pytest.raises(ConfigurationError):
        config._validate_company_entry(invalid_company, 0)

    # Invalid adapter
    invalid_adapter = {
        "id": "test-company",
        "name": "Test Company",
        "adapter": "invalid-adapter",
        "sources": [{"url": "https://example.com"}],
    }
    with pytest.raises(ConfigurationError) as exc_info:
        config._validate_company_entry(invalid_adapter, 0)
    assert "invalid adapter" in str(exc_info.value).lower()
