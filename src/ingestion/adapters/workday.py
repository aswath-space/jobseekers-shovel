"""
Workday ATS adapter.

Fetches jobs from Workday job boards. Workday is more complex than
Greenhouse/Lever and may require POST requests with JSON payloads.
"""

import json
from datetime import datetime
from typing import List, Any, Dict
from urllib.parse import urlparse

from src.ingestion.adapters.base import ATSAdapter, RawJob, AdapterError
from src.ingestion.crawler import CrawlerError


class WorkdayAdapter(ATSAdapter):
    """
    Adapter for Workday ATS platform.

    Note: Workday implementations vary significantly by company.
    This adapter handles the most common API pattern but may need
    customization for specific companies.
    """

    def fetch_jobs(self, source_url: str, crawler) -> List[RawJob]:
        """
        Fetch jobs from Workday API.

        Args:
            source_url: Workday board URL
            crawler: HTTP crawler instance

        Returns:
            List of RawJob objects

        Raises:
            AdapterError: If fetching or parsing fails
        """
        # Try to construct API endpoint from board URL
        api_url = self._construct_api_url(source_url)

        self.logger.info(f"Fetching jobs from Workday: {api_url}")

        # Workday typically requires POST with JSON payload
        payload = {
            "appliedFacets": {},
            "limit": 100,  # Fetch up to 100 jobs
            "offset": 0,
            "searchText": "",
        }

        try:
            response = crawler.session.post(
                api_url,
                json=payload,
                timeout=crawler.timeout,
                headers={
                    **crawler.session.headers,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        except CrawlerError as e:
            raise AdapterError(
                f"Failed to fetch jobs: {e}",
                adapter_name="Workday",
                source_url=api_url,
            ) from e

        except json.JSONDecodeError as e:
            raise AdapterError(
                f"Failed to parse JSON response: {e}",
                adapter_name="Workday",
                source_url=api_url,
            ) from e

        except Exception as e:
            raise AdapterError(
                f"Request failed: {e}",
                adapter_name="Workday",
                source_url=api_url,
            ) from e

        # Extract jobs from response
        jobs_data = data.get("jobPostings", [])

        if not isinstance(jobs_data, list):
            # Try alternate structure
            jobs_data = data.get("jobs", [])

        if not isinstance(jobs_data, list):
            self.logger.warning(
                f"Could not find job listings in Workday response. "
                f"Response keys: {list(data.keys())}"
            )
            jobs_data = []

        self.logger.info(f"Found {len(jobs_data)} jobs from Workday")

        # Convert to RawJob objects
        raw_jobs = []
        for job_data in jobs_data:
            try:
                raw_job = self._parse_job(job_data, source_url)
                raw_jobs.append(raw_job)
            except Exception as e:
                job_id = job_data.get("bulletFields", ["unknown"])[0] if "bulletFields" in job_data else "unknown"
                self.logger.warning(
                    f"Failed to parse job (ID: {job_id}): {e}"
                )
                continue

        return raw_jobs

    def _construct_api_url(self, board_url: str) -> str:
        """
        Construct Workday API URL from board URL.

        Args:
            board_url: Board URL (e.g., https://company.wd1.myworkdayjobs.com/en-US/Site)

        Returns:
            API URL for fetching jobs

        Example:
            Input: https://company.wd1.myworkdayjobs.com/en-US/External
            Output: https://company.wd1.myworkdayjobs.com/wday/cxs/company/External/jobs
        """
        parsed = urlparse(board_url)
        host = parsed.netloc  # e.g., company.wd1.myworkdayjobs.com
        path_parts = parsed.path.strip("/").split("/")

        # Extract company and site from URL
        # Typical format: /en-US/{site-name}
        if len(path_parts) >= 2:
            site_name = path_parts[-1]  # Last part is site name
        else:
            raise AdapterError(
                f"Could not extract site name from Workday URL: {board_url}",
                adapter_name="Workday",
                source_url=board_url,
            )

        # Extract company from hostname
        # Format: {company}.wd1.myworkdayjobs.com
        company = host.split(".")[0]

        # Construct API URL
        api_url = f"https://{host}/wday/cxs/{company}/{site_name}/jobs"
        return api_url

    def _parse_job(self, job_data: Dict[str, Any], base_url: str) -> RawJob:
        """
        Parse Workday job data into RawJob.

        Args:
            job_data: Raw job data from Workday API
            base_url: Base URL for constructing absolute URLs

        Returns:
            RawJob object
        """
        # Required fields - Workday structure can vary
        title = job_data.get("title", "Unknown Title")
        location = self.normalize_location(job_data.get("locationsText"))

        # Construct full URL
        external_path = job_data.get("externalPath", "")
        parsed_base = urlparse(base_url)
        base_host = f"{parsed_base.scheme}://{parsed_base.netloc}"
        url = f"{base_host}{external_path}" if external_path else base_url

        # Optional fields
        job_req_id = job_data.get("bulletFields", [None])[0] if "bulletFields" in job_data else None
        if not job_req_id:
            job_req_id = job_data.get("jobReqId")

        posted_str = job_data.get("postedOn")
        posted_date = None
        if posted_str:
            try:
                posted_date = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                self.logger.debug(f"Could not parse postedOn: {posted_str}")

        return RawJob(
            company_id=self.company_id,
            company_name=self.company_name,
            title=title,
            location=location,
            url=url,
            source_identifier=job_req_id,
            posted_date=posted_date,
            raw_data=job_data,
        )

    def normalize_location(self, location_data: Any) -> str:
        """
        Normalize Workday location data to string.

        Args:
            location_data: Location string from Workday

        Returns:
            Normalized location string
        """
        if isinstance(location_data, str):
            return location_data

        if isinstance(location_data, list) and location_data:
            return ", ".join(str(loc) for loc in location_data)

        return "Unknown Location"
