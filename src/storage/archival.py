"""
Data retention and archival utilities.

Handles archiving old closed jobs and maintaining database size.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

from src.processing.classifier import ClassifiedJob, JobStatus
from src.storage.job_store import JobStore
from src.utils.logging import get_logger


class JobArchiver:
    """
    Manages job data archival and retention policies.

    Archives closed jobs older than retention period to separate files.
    """

    def __init__(
        self,
        data_dir: str = "data/jobs",
        archive_dir: str = "data/archive",
        retention_days: int = 180
    ):
        """
        Initialize archiver.

        Args:
            data_dir: Active job data directory
            archive_dir: Archive directory
            retention_days: Days to retain closed jobs before archiving
        """
        self.data_dir = Path(data_dir)
        self.archive_dir = Path(archive_dir)
        self.retention_days = retention_days
        self.logger = get_logger(__name__)

        # Ensure directories exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def archive_old_jobs(
        self,
        jobs: Dict[str, ClassifiedJob],
        current_time: datetime = None
    ) -> Dict[str, int]:
        """
        Archive closed jobs older than retention period.

        Args:
            jobs: Current jobs dictionary
            current_time: Current timestamp

        Returns:
            Dictionary with archive statistics
        """
        if current_time is None:
            current_time = datetime.utcnow()

        cutoff_date = current_time - timedelta(days=self.retention_days)

        # Find jobs eligible for archiving
        to_archive = []
        for job_id, job in list(jobs.items()):
            if (job.status == JobStatus.CLOSED and
                job.last_seen < cutoff_date):
                to_archive.append(job)

        if not to_archive:
            self.logger.info("No jobs eligible for archiving")
            return {"archived": 0, "remaining": len(jobs)}

        # Archive by month
        archived_count = 0
        for job in to_archive:
            try:
                self._archive_job(job)
                del jobs[job.id]
                archived_count += 1
            except Exception as e:
                self.logger.error(f"Failed to archive job {job.id}: {e}")

        self.logger.info(
            f"Archived {archived_count} jobs older than {self.retention_days} days"
        )

        return {
            "archived": archived_count,
            "remaining": len(jobs),
            "cutoff_date": cutoff_date.isoformat()
        }

    def _archive_job(self, job: ClassifiedJob) -> None:
        """Archive a single job to monthly archive file."""
        # Determine archive file based on last_seen month
        year_month = job.last_seen.strftime("%Y-%m")
        archive_file = self.archive_dir / f"jobs-{year_month}.json"

        # Load existing archive or create new
        if archive_file.exists():
            with open(archive_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            jobs_list = data.get("jobs", [])
        else:
            jobs_list = []
            data = {
                "version": "1.0.0",
                "archive_month": year_month,
                "jobs": jobs_list
            }

        # Add job to archive
        job_dict = {
            "id": job.id,
            "company_id": job.company_id,
            "company_name": job.company_name,
            "title": job.title,
            "location": job.location,
            "signature": job.signature,
            "classification": job.classification.value,
            "first_seen": job.first_seen.isoformat(),
            "last_seen": job.last_seen.isoformat(),
            "archived_at": datetime.utcnow().isoformat()
        }
        jobs_list.append(job_dict)

        # Write archive
        data["jobs"] = jobs_list
        data["job_count"] = len(jobs_list)

        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.debug(f"Archived job {job.id} to {archive_file}")
