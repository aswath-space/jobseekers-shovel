"""
Configuration loading and validation utilities.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

import yaml


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """Configuration loader and accessor."""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration loader.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._companies_config = None
        self._ingestion_config = None

    def load_companies(self) -> List[Dict[str, Any]]:
        """
        Load company watchlist configuration.

        Returns:
            List of company configuration dictionaries

        Raises:
            ConfigurationError: If config file is missing or invalid
        """
        if self._companies_config is not None:
            return self._companies_config

        config_path = self.config_dir / "companies.yml"

        if not config_path.exists():
            raise ConfigurationError(
                f"Company configuration not found at {config_path}. "
                f"Copy companies.example.yml to companies.yml and configure."
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse companies.yml: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("companies.yml must contain a YAML dictionary")

        if "version" not in data:
            raise ConfigurationError("companies.yml missing required 'version' field")

        if "companies" not in data:
            raise ConfigurationError("companies.yml missing required 'companies' field")

        companies = data["companies"]
        if not isinstance(companies, list):
            raise ConfigurationError("'companies' must be a list")

        # Validate each company entry
        for i, company in enumerate(companies):
            self._validate_company_entry(company, i)

        self._companies_config = companies
        return companies

    def load_ingestion_config(self) -> Dict[str, Any]:
        """
        Load ingestion configuration.

        Returns:
            Ingestion configuration dictionary

        Raises:
            ConfigurationError: If config file is missing or invalid
        """
        if self._ingestion_config is not None:
            return self._ingestion_config

        config_path = self.config_dir / "ingestion.yml"

        if not config_path.exists():
            raise ConfigurationError(
                f"Ingestion configuration not found at {config_path}"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse ingestion.yml: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("ingestion.yml must contain a YAML dictionary")

        if "version" not in data:
            raise ConfigurationError("ingestion.yml missing required 'version' field")

        self._ingestion_config = data
        return data

    def _validate_company_entry(self, company: Dict[str, Any], index: int) -> None:
        """
        Validate a single company configuration entry.

        Args:
            company: Company configuration dictionary
            index: Index in the companies list (for error messages)

        Raises:
            ConfigurationError: If entry is invalid
        """
        required_fields = ["id", "name", "adapter", "sources"]

        for field in required_fields:
            if field not in company:
                raise ConfigurationError(
                    f"Company at index {index} missing required field: {field}"
                )

        # Validate ID format (alphanumeric and hyphens only)
        company_id = company["id"]
        if not isinstance(company_id, str) or not company_id:
            raise ConfigurationError(
                f"Company at index {index} has invalid 'id' (must be non-empty string)"
            )

        # Validate adapter
        valid_adapters = ["greenhouse", "lever", "workday"]
        adapter = company["adapter"]
        if adapter not in valid_adapters:
            raise ConfigurationError(
                f"Company '{company_id}' has invalid adapter '{adapter}'. "
                f"Valid adapters: {', '.join(valid_adapters)}"
            )

        # Validate sources
        sources = company["sources"]
        if not isinstance(sources, list) or not sources:
            raise ConfigurationError(
                f"Company '{company_id}' must have at least one source"
            )

        for source in sources:
            if not isinstance(source, dict) or "url" not in source:
                raise ConfigurationError(
                    f"Company '{company_id}' has invalid source (must have 'url' field)"
                )

    def get_company_by_id(self, company_id: str) -> Dict[str, Any]:
        """
        Get company configuration by ID.

        Args:
            company_id: Company identifier

        Returns:
            Company configuration dictionary

        Raises:
            ConfigurationError: If company not found
        """
        companies = self.load_companies()

        for company in companies:
            if company["id"] == company_id:
                return company

        raise ConfigurationError(f"Company not found: {company_id}")

    def get_config_value(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation path.

        Args:
            path: Dot-separated path (e.g., "crawling.request_delay_seconds")
            default: Default value if path not found

        Returns:
            Configuration value or default

        Example:
            >>> config = Config()
            >>> delay = config.get_config_value("crawling.request_delay_seconds", 1)
        """
        ingestion = self.load_ingestion_config()

        parts = path.split(".")
        current = ingestion

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current


# Global config instance
_config_instance = None


def get_config(config_dir: str = "config") -> Config:
    """
    Get or create global configuration instance.

    Args:
        config_dir: Directory containing configuration files

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_dir)
    return _config_instance
