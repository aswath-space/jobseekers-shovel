"""
Lever ATS adapter.

Fetches jobs from Lever job boards via their JSON API.
"""

import json
from datetime import datetime
from typing import List, Any, Dict

from src.ingestion.adapters.base import ATSAdapter, RawJob, AdapterError
from src.ingestion.crawler import CrawlerError


class LeverAdapter(ATSAdapter):
    """
    Adapter for Lever ATS platform.

    API Documentation: https://github.com/lever/postings-api
    """

    def fetch_jobs(self, source_url: str, crawler) -> List[RawJob]:
        """
        Fetch jobs from Lever API.

        Args:
            source_url: Lever board URL (e.g., https://jobs.lever.co/company)
            crawler: HTTP crawler instance

        Returns:
            List of RawJob objects

        Raises:
            AdapterError: If fetching or parsing fails
        """
        # Convert board URL to API URL
        api_url = self._convert_to_api_url(source_url)

        self.logger.info(f"Fetching jobs from Lever: {api_url}")

        try:
            response = crawler.get(api_url)
            data = response.json()

        except CrawlerError as e:
            raise AdapterError(
                f"Failed to fetch jobs: {e}",
                adapter_name="Lever",
                source_url=api_url,
            ) from e

        except json.JSONDecodeError as e:
            raise AdapterError(
                f"Failed to parse JSON response: {e}",
                adapter_name="Lever",
                source_url=api_url,
            ) from e

        # Lever API returns array directly
        if not isinstance(data, list):
            raise AdapterError(
                f"Unexpected response format: expected array, got {type(data).__name__}",
                adapter_name="Lever",
                source_url=api_url,
            )

        self.logger.info(f"Found {len(data)} jobs from Lever")

        # Convert to RawJob objects
        raw_jobs = []
        for job_data in data:
            try:
                raw_job = self._parse_job(job_data)
                raw_jobs.append(raw_job)
            except Exception as e:
                self.logger.warning(
                    f"Failed to parse job (ID: {job_data.get('id', 'unknown')}): {e}"
                )
                continue

        return raw_jobs

    def _convert_to_api_url(self, board_url: str) -> str:
        """
        Convert Lever board URL to API URL.

        Args:
            board_url: Board URL (e.g., https://jobs.lever.co/company)

        Returns:
            API URL with ?mode=json parameter
        """
        # Check if already has query parameters
        if "?" in board_url:
            # Append mode=json
            separator = "&" if not board_url.endswith("?") else ""
            return f"{board_url}{separator}mode=json"
        else:
            # Add ?mode=json
            return f"{board_url}?mode=json"

    def _parse_job(self, job_data: Dict[str, Any]) -> RawJob:
        """
        Parse Lever job data into RawJob.

        Args:
            job_data: Raw job data from Lever API

        Returns:
            RawJob object
        """
        # Required fields
        job_id = job_data["id"]
        title = job_data["text"]
        location = self.normalize_location(job_data.get("categories", {}))
        url = job_data["hostedUrl"]

        # Optional fields - Lever uses milliseconds since epoch
        created_ms = job_data.get("createdAt")
        posted_date = None
        if created_ms:
            try:
                posted_date = datetime.fromtimestamp(created_ms / 1000.0)
            except (ValueError, TypeError):
                self.logger.debug(f"Could not parse createdAt: {created_ms}")

        # Extract department/team
        categories = job_data.get("categories", {})
        department = categories.get("team")

        return RawJob(
            company_id=self.company_id,
            company_name=self.company_name,
            title=title,
            location=location,
            url=url,
            source_identifier=job_id,
            posted_date=posted_date,
            department=department,
            raw_data=job_data,
        )

    def normalize_location(self, categories: Any) -> str:
        """
        Normalize Lever location data to string.

        Args:
            categories: Categories object from Lever (dict with 'location' field)

        Returns:
            Normalized location string
        """
        if isinstance(categories, dict):
            location = categories.get("location")
            if location:
                return str(location)

        return "Unknown Location"
