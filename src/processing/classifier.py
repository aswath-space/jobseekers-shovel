"""
Job classification engine.

Classifies jobs as New, Repost, or Existing based on signatures and temporal data.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum

from src.processing.normalizer import JobNormalizer
from src.processing.matcher import JobMatcher
from src.ingestion.adapters.base import RawJob
from src.utils.logging import get_logger


class JobClassification(Enum):
    """Job classification types."""
    NEW = "new"
    REPOST = "repost"
    EXISTING = "existing"


class JobStatus(Enum):
    """Job lifecycle status."""
    ACTIVE = "active"
    MISSING = "missing"
    CLOSED = "closed"
    REOPENED = "reopened"


@dataclass
class ClassifiedJob:
    """
    Fully classified job with temporal tracking.
    """
    # Core identification
    id: str  # Internal UUID
    company_id: str
    company_name: str
    title: str
    location: str
    url: str
    signature: str

    # Classification
    classification: JobClassification
    classification_reasoning: str
    status: JobStatus

    # Temporal tracking
    first_seen: datetime
    last_seen: datetime
    observations: List[Dict[str, Any]]

    # Optional fields
    source_identifier: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JobClassifier:
    """
    Classifies jobs and tracks them over time.

    Combines normalization, fuzzy matching, and temporal tracking to:
    1. Detect new jobs
    2. Identify reposts (same job, different ID)
    3. Track existing jobs
    4. Manage job lifecycle (active/missing/closed/reopened)
    """

    def __init__(
        self,
        repost_window_days: int = 30,
        similarity_threshold: float = 0.90
    ):
        """
        Initialize classifier.

        Args:
            repost_window_days: Days to look back for repost detection
            similarity_threshold: Fuzzy match threshold for reposts
        """
        self.repost_window_days = repost_window_days
        self.normalizer = JobNormalizer()
        self.matcher = JobMatcher(similarity_threshold=similarity_threshold)
        self.logger = get_logger(__name__)

        # In-memory job database (would be loaded from JSON in real usage)
        self.known_jobs: Dict[str, ClassifiedJob] = {}

    def classify_job(
        self,
        raw_job: RawJob,
        current_time: Optional[datetime] = None
    ) -> ClassifiedJob:
        """
        Classify a raw job posting.

        Steps:
        1. Normalize signature
        2. Check for exact ID match (existing)
        3. Check for signature match within repost window (repost)
        4. Otherwise, classify as new

        Args:
            raw_job: Raw job from adapter
            current_time: Current timestamp (defaults to now)

        Returns:
            Classified job with reasoning
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Create normalized signature
        signature = self.normalizer.create_signature(
            company_id=raw_job.company_id,
            title=raw_job.title,
            location=raw_job.location
        )

        # Check for exact ID match first
        existing_job = self._find_by_source_id(
            raw_job.company_id,
            raw_job.source_identifier
        )

        if existing_job:
            # Update existing job
            return self._update_existing_job(existing_job, raw_job, current_time)

        # Check for signature match (potential repost)
        similar_job = self._find_similar_recent_job(
            signature,
            raw_job.company_id,
            current_time
        )

        if similar_job:
            # Likely a repost
            return self._classify_as_repost(
                raw_job,
                signature,
                similar_job,
                current_time
            )

        # Check if this is a reopened job (closed job reappearing)
        closed_job = self._find_closed_similar_job(
            signature,
            raw_job.company_id
        )

        if closed_job:
            return self._classify_as_reopened(
                raw_job,
                signature,
                closed_job,
                current_time
            )

        # Brand new job
        return self._classify_as_new(raw_job, signature, current_time)

    def _find_by_source_id(
        self,
        company_id: str,
        source_identifier: Optional[str]
    ) -> Optional[ClassifiedJob]:
        """Find job by source identifier."""
        if not source_identifier:
            return None

        for job in self.known_jobs.values():
            if (job.company_id == company_id and
                job.source_identifier == source_identifier):
                return job

        return None

    def _find_similar_recent_job(
        self,
        signature: str,
        company_id: str,
        current_time: datetime
    ) -> Optional[ClassifiedJob]:
        """Find similar job within repost window."""
        cutoff_time = current_time - timedelta(days=self.repost_window_days)

        # Get recent jobs for same company
        recent_jobs = [
            job for job in self.known_jobs.values()
            if (job.company_id == company_id and
                job.last_seen >= cutoff_time and
                job.status != JobStatus.CLOSED)
        ]

        if not recent_jobs:
            return None

        # Find best matching signature
        signatures = [job.signature for job in recent_jobs]
        best_match = self.matcher.find_best_match(signature, signatures)

        if best_match:
            # Return the job with matching signature
            for job in recent_jobs:
                if job.signature == best_match:
                    return job

        return None

    def _find_closed_similar_job(
        self,
        signature: str,
        company_id: str
    ) -> Optional[ClassifiedJob]:
        """Find similar closed job (for reopened detection)."""
        closed_jobs = [
            job for job in self.known_jobs.values()
            if (job.company_id == company_id and
                job.status == JobStatus.CLOSED)
        ]

        if not closed_jobs:
            return None

        signatures = [job.signature for job in closed_jobs]
        best_match = self.matcher.find_best_match(signature, signatures)

        if best_match:
            for job in closed_jobs:
                if job.signature == best_match:
                    return job

        return None

    def _update_existing_job(
        self,
        existing_job: ClassifiedJob,
        raw_job: RawJob,
        current_time: datetime
    ) -> ClassifiedJob:
        """Update an existing job's last_seen time."""
        existing_job.last_seen = current_time
        existing_job.updated_at = current_time

        # Add observation
        existing_job.observations.append({
            "timestamp": current_time.isoformat(),
            "source_identifier": raw_job.source_identifier,
            "url": raw_job.url,
        })

        # If job was missing, mark as active again
        if existing_job.status == JobStatus.MISSING:
            existing_job.status = JobStatus.ACTIVE
            self.logger.info(f"Job {existing_job.id} returned (was missing)")

        self.logger.debug(
            f"Updated existing job: {existing_job.title} at {existing_job.company_name}"
        )

        return existing_job

    def _classify_as_new(
        self,
        raw_job: RawJob,
        signature: str,
        current_time: datetime
    ) -> ClassifiedJob:
        """Classify job as new."""
        import uuid

        job_id = str(uuid.uuid4())

        classified = ClassifiedJob(
            id=job_id,
            company_id=raw_job.company_id,
            company_name=raw_job.company_name,
            title=raw_job.title,
            location=raw_job.location,
            url=raw_job.url,
            signature=signature,
            classification=JobClassification.NEW,
            classification_reasoning="New job posting (no previous match found)",
            status=JobStatus.ACTIVE,
            first_seen=current_time,
            last_seen=current_time,
            observations=[{
                "timestamp": current_time.isoformat(),
                "source_identifier": raw_job.source_identifier,
                "url": raw_job.url,
            }],
            source_identifier=raw_job.source_identifier,
            department=raw_job.department,
            description=raw_job.description,
            created_at=current_time,
            updated_at=current_time,
        )

        self.known_jobs[job_id] = classified

        self.logger.info(
            f"NEW: {raw_job.title} at {raw_job.company_name} ({raw_job.location})"
        )

        return classified

    def _classify_as_repost(
        self,
        raw_job: RawJob,
        signature: str,
        similar_job: ClassifiedJob,
        current_time: datetime
    ) -> ClassifiedJob:
        """Classify job as likely repost."""
        import uuid

        job_id = str(uuid.uuid4())

        similarity = self.matcher.calculate_similarity(
            signature,
            similar_job.signature
        )

        classified = ClassifiedJob(
            id=job_id,
            company_id=raw_job.company_id,
            company_name=raw_job.company_name,
            title=raw_job.title,
            location=raw_job.location,
            url=raw_job.url,
            signature=signature,
            classification=JobClassification.REPOST,
            classification_reasoning=(
                f"Likely repost of job {similar_job.id} "
                f"(similarity: {similarity:.2f}, first seen: {similar_job.first_seen.date()})"
            ),
            status=JobStatus.ACTIVE,
            first_seen=current_time,
            last_seen=current_time,
            observations=[{
                "timestamp": current_time.isoformat(),
                "source_identifier": raw_job.source_identifier,
                "url": raw_job.url,
            }],
            source_identifier=raw_job.source_identifier,
            department=raw_job.department,
            description=raw_job.description,
            created_at=current_time,
            updated_at=current_time,
        )

        self.known_jobs[job_id] = classified

        self.logger.info(
            f"REPOST: {raw_job.title} at {raw_job.company_name} "
            f"(similar to {similar_job.id}, similarity={similarity:.2f})"
        )

        return classified

    def _classify_as_reopened(
        self,
        raw_job: RawJob,
        signature: str,
        closed_job: ClassifiedJob,
        current_time: datetime
    ) -> ClassifiedJob:
        """Classify job as reopened (closed job reappearing)."""
        # Reopen the existing job rather than creating new
        closed_job.status = JobStatus.REOPENED
        closed_job.last_seen = current_time
        closed_job.updated_at = current_time
        closed_job.url = raw_job.url  # Update URL
        closed_job.source_identifier = raw_job.source_identifier

        closed_job.observations.append({
            "timestamp": current_time.isoformat(),
            "source_identifier": raw_job.source_identifier,
            "url": raw_job.url,
            "note": "Job reopened"
        })

        closed_job.classification_reasoning = (
            f"Job reopened (was closed on {closed_job.last_seen.date()}, "
            f"originally first seen {closed_job.first_seen.date()})"
        )

        self.logger.info(
            f"REOPENED: {raw_job.title} at {raw_job.company_name} "
            f"(was closed, now active again)"
        )

        return closed_job

    def mark_missing_jobs(
        self,
        observed_job_ids: List[str],
        current_time: Optional[datetime] = None
    ) -> int:
        """
        Mark jobs that weren't observed in this cycle as missing.

        Args:
            observed_job_ids: List of job IDs that were seen this cycle
            current_time: Current timestamp

        Returns:
            Number of jobs marked as missing
        """
        if current_time is None:
            current_time = datetime.utcnow()

        marked_count = 0

        for job_id, job in self.known_jobs.items():
            if (job_id not in observed_job_ids and
                job.status == JobStatus.ACTIVE):
                job.status = JobStatus.MISSING
                job.updated_at = current_time
                marked_count += 1

                self.logger.debug(
                    f"Marked missing: {job.title} at {job.company_name}"
                )

        return marked_count

    def close_old_missing_jobs(
        self,
        timeout_days: int,
        current_time: Optional[datetime] = None
    ) -> int:
        """
        Close jobs that have been missing for too long.

        Args:
            timeout_days: Days before marking as closed
            current_time: Current timestamp

        Returns:
            Number of jobs closed
        """
        if current_time is None:
            current_time = datetime.utcnow()

        cutoff_time = current_time - timedelta(days=timeout_days)
        closed_count = 0

        for job in self.known_jobs.values():
            if (job.status == JobStatus.MISSING and
                job.last_seen < cutoff_time):
                job.status = JobStatus.CLOSED
                job.updated_at = current_time
                closed_count += 1

                self.logger.info(
                    f"Closed: {job.title} at {job.company_name} "
                    f"(missing since {job.last_seen.date()})"
                )

        return closed_count
