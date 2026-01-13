"""
Job data storage using JSON files.

Handles reading/writing classified jobs to versioned JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.processing.classifier import ClassifiedJob, JobClassification, JobStatus
from src.storage.schema import JOB_RECORD_SCHEMA_V1, validate_job_record
from src.utils.logging import get_logger


class JobStore:
    """
    Manages persistent storage of classified jobs.

    Uses JSON files with schema versioning for backward compatibility.
    """

    def __init__(self, data_dir: str = "data/jobs", schema_version: str = "1.0.0"):
        """
        Initialize job store.

        Args:
            data_dir: Directory for job data files
            schema_version: Schema version to use (default: 1.0.0)
        """
        self.data_dir = Path(data_dir)
        self.schema_version = schema_version
        self.logger = get_logger(__name__)

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Determine file path based on version
        self.file_path = self.data_dir / f"jobs-v{schema_version.split('.')[0]}.json"

    def load_jobs(self) -> Dict[str, ClassifiedJob]:
        """
        Load all jobs from storage.

        Returns:
            Dictionary mapping job ID to ClassifiedJob
        """
        if not self.file_path.exists():
            self.logger.info(f"No existing job data found at {self.file_path}")
            return {}

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate schema version
            file_version = data.get("version", "unknown")
            if file_version != self.schema_version:
                self.logger.warning(
                    f"Schema version mismatch: file={file_version}, expected={self.schema_version}"
                )

            jobs_data = data.get("jobs", [])
            self.logger.info(f"Loaded {len(jobs_data)} jobs from {self.file_path}")

            # Convert to ClassifiedJob objects
            jobs = {}
            for job_dict in jobs_data:
                try:
                    # Validate against schema
                    validate_job_record(job_dict)

                    # Convert to ClassifiedJob
                    classified_job = self._dict_to_classified_job(job_dict)
                    jobs[classified_job.id] = classified_job

                except Exception as e:
                    self.logger.error(f"Error loading job {job_dict.get('id', 'unknown')}: {e}")
                    continue

            self.logger.info(f"Successfully loaded {len(jobs)} jobs")
            return jobs

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {self.file_path}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Error loading jobs from {self.file_path}: {e}")
            return {}

    def save_jobs(self, jobs: Dict[str, ClassifiedJob]) -> bool:
        """
        Save all jobs to storage.

        Args:
            jobs: Dictionary mapping job ID to ClassifiedJob

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to serializable format
            jobs_data = []
            for job in jobs.values():
                job_dict = self._classified_job_to_dict(job)
                jobs_data.append(job_dict)

            # Create data structure with metadata
            data = {
                "version": self.schema_version,
                "generated_at": datetime.utcnow().isoformat(),
                "job_count": len(jobs_data),
                "jobs": jobs_data
            }

            # Write to file (atomic write via temp file)
            temp_path = self.file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.file_path)

            self.logger.info(f"Saved {len(jobs_data)} jobs to {self.file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving jobs to {self.file_path}: {e}", exc_info=True)
            return False

    def _classified_job_to_dict(self, job: ClassifiedJob) -> dict:
        """Convert ClassifiedJob to dictionary."""
        return {
            "id": job.id,
            "company_id": job.company_id,
            "company_name": job.company_name,
            "title": job.title,
            "location": job.location,
            "url": job.url,
            "signature": job.signature,
            "classification": job.classification.value,
            "classification_reasoning": job.classification_reasoning,
            "status": job.status.value,
            "first_seen": job.first_seen.isoformat(),
            "last_seen": job.last_seen.isoformat(),
            "observations": job.observations,
            "source_identifier": job.source_identifier,
            "department": job.department,
            "description": job.description,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        }

    def _dict_to_classified_job(self, data: dict) -> ClassifiedJob:
        """Convert dictionary to ClassifiedJob."""
        return ClassifiedJob(
            id=data["id"],
            company_id=data["company_id"],
            company_name=data["company_name"],
            title=data["title"],
            location=data["location"],
            url=data["url"],
            signature=data["signature"],
            classification=JobClassification(data["classification"]),
            classification_reasoning=data["classification_reasoning"],
            status=JobStatus(data["status"]),
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            observations=data["observations"],
            source_identifier=data.get("source_identifier"),
            department=data.get("department"),
            description=data.get("description"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )

    def export_to_csv(self, output_path: str, jobs: Optional[Dict[str, ClassifiedJob]] = None) -> bool:
        """
        Export jobs to CSV format.

        Args:
            output_path: Path to CSV file
            jobs: Jobs to export (if None, loads from storage)

        Returns:
            True if successful, False otherwise
        """
        import csv

        if jobs is None:
            jobs = self.load_jobs()

        if not jobs:
            self.logger.warning("No jobs to export")
            return False

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                # Define CSV columns
                fieldnames = [
                    "id", "company_id", "company_name", "title", "location",
                    "department", "url", "classification", "status",
                    "first_seen", "last_seen", "signature"
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for job in jobs.values():
                    writer.writerow({
                        "id": job.id,
                        "company_id": job.company_id,
                        "company_name": job.company_name,
                        "title": job.title,
                        "location": job.location,
                        "department": job.department or "",
                        "url": job.url,
                        "classification": job.classification.value,
                        "status": job.status.value,
                        "first_seen": job.first_seen.isoformat(),
                        "last_seen": job.last_seen.isoformat(),
                        "signature": job.signature,
                    })

            self.logger.info(f"Exported {len(jobs)} jobs to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}", exc_info=True)
            return False
