"""
Greenhouse ATS adapter.

Fetches jobs from Greenhouse job boards via their JSON API.
"""

import json
from datetime import datetime
from typing import List, Any, Dict

from src.ingestion.adapters.base import ATSAdapter, RawJob, AdapterError
from src.ingestion.crawler import CrawlerError


class GreenhouseAdapter(ATSAdapter):
    """
    Adapter for Greenhouse ATS platform.

    API Documentation: https://developers.greenhouse.io/job-board.html
    """

    def fetch_jobs(self, source_url: str, crawler) -> List[RawJob]:
        """
        Fetch jobs from Greenhouse API.

        Args:
            source_url: Greenhouse board URL (e.g., https://boards.greenhouse.io/company)
            crawler: HTTP crawler instance

        Returns:
            List of RawJob objects

        Raises:
            AdapterError: If fetching or parsing fails
        """
        # Convert board URL to API URL
        api_url = self._convert_to_api_url(source_url)

        self.logger.info(f"Fetching jobs from Greenhouse: {api_url}")

        try:
            response = crawler.get(api_url)
            data = response.json()

        except CrawlerError as e:
            raise AdapterError(
                f"Failed to fetch jobs: {e}",
                adapter_name="Greenhouse",
                source_url=api_url,
            ) from e

        except json.JSONDecodeError as e:
            raise AdapterError(
                f"Failed to parse JSON response: {e}",
                adapter_name="Greenhouse",
                source_url=api_url,
            ) from e

        # Extract jobs from response
        jobs_data = data.get("jobs", [])

        if not isinstance(jobs_data, list):
            raise AdapterError(
                f"Unexpected response format: 'jobs' is not a list",
                adapter_name="Greenhouse",
                source_url=api_url,
            )

        self.logger.info(f"Found {len(jobs_data)} jobs from Greenhouse")

        # Convert to RawJob objects
        raw_jobs = []
        for job_data in jobs_data:
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
        Convert Greenhouse board URL to API URL.

        Args:
            board_url: Board URL (e.g., https://boards.greenhouse.io/company)

        Returns:
            API URL (e.g., https://boards-api.greenhouse.io/v1/boards/company/jobs)
        """
        # Extract company slug from URL
        # Format: https://boards.greenhouse.io/{company}
        if "boards.greenhouse.io/" in board_url:
            company_slug = board_url.split("boards.greenhouse.io/")[-1].rstrip("/")
            return f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"

        # Already an API URL
        if "boards-api.greenhouse.io" in board_url:
            return board_url

        raise AdapterError(
            f"Invalid Greenhouse URL format: {board_url}",
            adapter_name="Greenhouse",
            source_url=board_url,
        )

    def _parse_job(self, job_data: Dict[str, Any]) -> RawJob:
        """
        Parse Greenhouse job data into RawJob.

        Args:
            job_data: Raw job data from Greenhouse API

        Returns:
            RawJob object
        """
        # Required fields
        job_id = str(job_data["id"])
        title = job_data["title"]
        location_data = job_data.get("location", {})
        location = self.normalize_location(location_data)
        url = job_data["absolute_url"]

        # Optional fields
        updated_str = job_data.get("updated_at")
        updated_date = None
        if updated_str:
            try:
                updated_date = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                self.logger.debug(f"Could not parse updated_at: {updated_str}")

        # Extract department
        departments = job_data.get("departments", [])
        department = None
        if departments and isinstance(departments, list) and len(departments) > 0:
            department = departments[0].get("name")

        return RawJob(
            company_id=self.company_id,
            company_name=self.company_name,
            title=title,
            location=location,
            url=url,
            source_identifier=job_id,
            updated_date=updated_date,
            department=department,
            raw_data=job_data,
        )

    def normalize_location(self, location_data: Any) -> str:
        """
        Normalize Greenhouse location data to string.

        Args:
            location_data: Location object from Greenhouse (dict with 'name' field)

        Returns:
            Normalized location string
        """
        if isinstance(location_data, dict):
            return location_data.get("name", "Unknown Location")

        if isinstance(location_data, str):
            return location_data

        return "Unknown Location"
