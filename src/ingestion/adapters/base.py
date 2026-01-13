"""
Base adapter interface for ATS platforms.

All ATS-specific adapters must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.utils.logging import get_logger


@dataclass
class RawJob:
    """
    Standardized job data structure returned by all adapters.

    This represents the raw job data before processing/classification.
    """

    # Required fields
    company_id: str  # References company in config
    company_name: str
    title: str
    location: str
    url: str

    # Optional fields
    source_identifier: Optional[str] = None  # ATS-specific job ID
    posted_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    department: Optional[str] = None
    description: Optional[str] = None

    # Raw data for debugging
    raw_data: Optional[Dict[str, Any]] = None


class ATSAdapter(ABC):
    """
    Base class for ATS platform adapters.

    Each ATS platform (Greenhouse, Lever, Workday, etc.) implements
    this interface to provide a consistent way to fetch job postings.
    """

    def __init__(self, company_id: str, company_name: str):
        """
        Initialize adapter.

        Args:
            company_id: Company identifier from config
            company_name: Company display name
        """
        self.company_id = company_id
        self.company_name = company_name
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def fetch_jobs(self, source_url: str, crawler) -> List[RawJob]:
        """
        Fetch all job postings from the ATS platform.

        Args:
            source_url: URL to fetch jobs from
            crawler: HTTP crawler instance for making requests

        Returns:
            List of RawJob objects

        Raises:
            AdapterError: If fetching or parsing fails
        """
        pass

    @abstractmethod
    def normalize_location(self, location_data: Any) -> str:
        """
        Normalize location data to a standard string format.

        Args:
            location_data: Platform-specific location data (string, object, array, etc.)

        Returns:
            Normalized location string (e.g., "San Francisco, CA" or "Remote")
        """
        pass

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL for logging/debugging.

        Args:
            url: Full URL

        Returns:
            Domain string
        """
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc


class AdapterError(Exception):
    """Raised when an adapter encounters an error."""

    def __init__(self, message: str, adapter_name: str, source_url: str = None):
        """
        Initialize adapter error.

        Args:
            message: Error message
            adapter_name: Name of the adapter that raised the error
            source_url: Optional URL that caused the error
        """
        self.adapter_name = adapter_name
        self.source_url = source_url
        super().__init__(f"[{adapter_name}] {message}")


def create_adapter(adapter_type: str, company_id: str, company_name: str) -> ATSAdapter:
    """
    Factory function to create appropriate adapter based on type.

    Args:
        adapter_type: Type of adapter (e.g., "greenhouse", "lever", "workday")
        company_id: Company identifier
        company_name: Company display name

    Returns:
        Initialized adapter instance

    Raises:
        ValueError: If adapter_type is not recognized
    """
    # Import here to avoid circular dependencies
    from src.ingestion.adapters.greenhouse import GreenhouseAdapter
    from src.ingestion.adapters.lever import LeverAdapter
    from src.ingestion.adapters.workday import WorkdayAdapter

    adapters = {
        "greenhouse": GreenhouseAdapter,
        "lever": LeverAdapter,
        "workday": WorkdayAdapter,
    }

    adapter_class = adapters.get(adapter_type.lower())
    if not adapter_class:
        raise ValueError(
            f"Unknown adapter type: {adapter_type}. "
            f"Valid types: {', '.join(adapters.keys())}"
        )

    return adapter_class(company_id, company_name)
