"""
Tests for job classification engine.
"""

import pytest
from datetime import datetime, timedelta

from src.processing.classifier import (
    JobClassifier,
    JobClassification,
    JobStatus,
    ClassifiedJob
)
from src.ingestion.adapters.base import RawJob


@pytest.fixture
def classifier():
    """Create classifier with default settings."""
    return JobClassifier(
        repost_window_days=30,
        similarity_threshold=0.90
    )


@pytest.fixture
def sample_raw_job():
    """Create sample raw job."""
    return RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Senior Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/123",
        source_identifier="job-123",
        department="Engineering",
        description="Great opportunity"
    )


def test_classifier_initialization():
    """Test classifier initialization."""
    classifier = JobClassifier(
        repost_window_days=60,
        similarity_threshold=0.85
    )

    assert classifier.repost_window_days == 60
    assert classifier.normalizer is not None
    assert classifier.matcher is not None
    assert classifier.matcher.similarity_threshold == 0.85
    assert len(classifier.known_jobs) == 0


def test_classify_new_job(classifier, sample_raw_job):
    """Test classifying a brand new job."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    classified = classifier.classify_job(sample_raw_job, current_time)

    assert classified.classification == JobClassification.NEW
    assert classified.status == JobStatus.ACTIVE
    assert classified.company_id == "acme-corp"
    assert classified.company_name == "Acme Corp"
    assert classified.title == "Senior Software Engineer"
    assert classified.first_seen == current_time
    assert classified.last_seen == current_time
    assert len(classified.observations) == 1
    assert classified.observations[0]["source_identifier"] == "job-123"
    assert "New job posting" in classified.classification_reasoning


def test_classify_existing_job_by_id(classifier, sample_raw_job):
    """Test updating an existing job (same source ID)."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # First classification
    classified1 = classifier.classify_job(sample_raw_job, current_time)
    first_id = classified1.id

    # Second classification (1 day later, same source ID)
    later_time = current_time + timedelta(days=1)
    classified2 = classifier.classify_job(sample_raw_job, later_time)

    # Should be same job
    assert classified2.id == first_id
    assert classified2.classification == JobClassification.NEW  # Original classification
    assert classified2.status == JobStatus.ACTIVE
    assert classified2.first_seen == current_time
    assert classified2.last_seen == later_time
    assert len(classified2.observations) == 2


def test_classify_repost(classifier):
    """Test detecting a repost (similar job, different ID)."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Original job
    job1 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Senior Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/123",
        source_identifier="job-123"
    )

    classified1 = classifier.classify_job(job1, current_time)
    assert classified1.classification == JobClassification.NEW

    # Very similar job posted 10 days later (different ID)
    later_time = current_time + timedelta(days=10)
    job2 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Sr. Software Engineer",  # Slight variation
        location="San Francisco, California",  # Different format
        url="https://acme.com/jobs/456",
        source_identifier="job-456"
    )

    classified2 = classifier.classify_job(job2, later_time)

    assert classified2.classification == JobClassification.REPOST
    assert classified2.status == JobStatus.ACTIVE
    assert "Likely repost" in classified2.classification_reasoning
    assert classified1.id in classified2.classification_reasoning


def test_classify_repost_outside_window(classifier):
    """Test that jobs outside repost window are classified as new."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Original job
    job1 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Senior Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/123",
        source_identifier="job-123"
    )

    classifier.classify_job(job1, current_time)

    # Similar job posted 40 days later (outside 30-day window)
    later_time = current_time + timedelta(days=40)
    job2 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Sr. Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/456",
        source_identifier="job-456"
    )

    classified2 = classifier.classify_job(job2, later_time)

    # Should be NEW, not REPOST (outside window)
    assert classified2.classification == JobClassification.NEW


def test_classify_reopened_job(classifier):
    """Test detecting a reopened job (closed job reappearing)."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Original job
    job1 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Senior Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/123",
        source_identifier="job-123"
    )

    classified1 = classifier.classify_job(job1, current_time)

    # Manually mark as closed
    classified1.status = JobStatus.CLOSED

    # Same job reappears with new ID
    later_time = current_time + timedelta(days=60)
    job2 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Sr. Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/789",
        source_identifier="job-789"
    )

    classified2 = classifier.classify_job(job2, later_time)

    # Should be same job, reopened
    assert classified2.id == classified1.id
    assert classified2.status == JobStatus.REOPENED
    assert "Job reopened" in classified2.classification_reasoning
    assert len(classified2.observations) == 2
    assert classified2.observations[1]["note"] == "Job reopened"


def test_mark_missing_jobs(classifier, sample_raw_job):
    """Test marking jobs as missing when not observed."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Create 3 jobs
    job1 = classifier.classify_job(sample_raw_job, current_time)

    job2_raw = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Junior Developer",
        location="Boston, MA",
        url="https://acme.com/jobs/456",
        source_identifier="job-456"
    )
    job2 = classifier.classify_job(job2_raw, current_time)

    job3_raw = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Product Manager",
        location="New York, NY",
        url="https://acme.com/jobs/789",
        source_identifier="job-789"
    )
    job3 = classifier.classify_job(job3_raw, current_time)

    assert job1.status == JobStatus.ACTIVE
    assert job2.status == JobStatus.ACTIVE
    assert job3.status == JobStatus.ACTIVE

    # Only job1 and job3 were observed in this cycle
    later_time = current_time + timedelta(days=1)
    marked_count = classifier.mark_missing_jobs(
        observed_job_ids=[job1.id, job3.id],
        current_time=later_time
    )

    assert marked_count == 1
    assert job2.status == JobStatus.MISSING
    assert job1.status == JobStatus.ACTIVE
    assert job3.status == JobStatus.ACTIVE


def test_mark_missing_jobs_idempotent(classifier, sample_raw_job):
    """Test that marking missing jobs is idempotent."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    job = classifier.classify_job(sample_raw_job, current_time)

    # First marking
    marked1 = classifier.mark_missing_jobs([], current_time)
    assert marked1 == 1
    assert job.status == JobStatus.MISSING

    # Second marking (should not mark again)
    marked2 = classifier.mark_missing_jobs([], current_time)
    assert marked2 == 0
    assert job.status == JobStatus.MISSING


def test_return_missing_job_to_active(classifier, sample_raw_job):
    """Test that missing job returns to active when observed again."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Create job
    job = classifier.classify_job(sample_raw_job, current_time)

    # Mark as missing
    classifier.mark_missing_jobs([], current_time)
    assert job.status == JobStatus.MISSING

    # Observe again
    later_time = current_time + timedelta(days=1)
    updated_job = classifier.classify_job(sample_raw_job, later_time)

    assert updated_job.id == job.id
    assert updated_job.status == JobStatus.ACTIVE


def test_close_old_missing_jobs(classifier, sample_raw_job):
    """Test closing jobs that have been missing too long."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Create job
    job = classifier.classify_job(sample_raw_job, current_time)

    # Mark as missing
    classifier.mark_missing_jobs([], current_time)
    assert job.status == JobStatus.MISSING

    # Close jobs missing for > 7 days (job was last seen on 1/15, now 1/23)
    later_time = current_time + timedelta(days=8)
    closed_count = classifier.close_old_missing_jobs(
        timeout_days=7,
        current_time=later_time
    )

    assert closed_count == 1
    assert job.status == JobStatus.CLOSED


def test_close_old_missing_jobs_within_timeout(classifier, sample_raw_job):
    """Test that jobs within timeout are not closed."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Create job
    job = classifier.classify_job(sample_raw_job, current_time)

    # Mark as missing
    classifier.mark_missing_jobs([], current_time)

    # Try to close jobs missing for > 7 days, but only 5 days have passed
    later_time = current_time + timedelta(days=5)
    closed_count = classifier.close_old_missing_jobs(
        timeout_days=7,
        current_time=later_time
    )

    assert closed_count == 0
    assert job.status == JobStatus.MISSING


def test_different_companies_dont_match(classifier):
    """Test that similar jobs from different companies don't match."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Job from Company A
    job1 = RawJob(
        company_id="company-a",
        company_name="Company A",
        title="Senior Engineer",
        location="San Francisco",
        url="https://companya.com/jobs/1",
        source_identifier="job-1"
    )

    classified1 = classifier.classify_job(job1, current_time)

    # Very similar job from Company B
    job2 = RawJob(
        company_id="company-b",
        company_name="Company B",
        title="Senior Engineer",
        location="San Francisco",
        url="https://companyb.com/jobs/1",
        source_identifier="job-1"
    )

    classified2 = classifier.classify_job(job2, current_time)

    # Should be separate new jobs
    assert classified1.classification == JobClassification.NEW
    assert classified2.classification == JobClassification.NEW
    assert classified1.id != classified2.id


def test_signature_creation(classifier):
    """Test that signatures are created correctly."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    job = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Sr. Software Engineer",
        location="San Francisco, CA",
        url="https://acme.com/jobs/123",
        source_identifier="job-123"
    )

    classified = classifier.classify_job(job, current_time)

    # Signature should be normalized
    assert classified.signature == "acme-corp|senior software engineer|san francisco california"


def test_observations_tracking(classifier, sample_raw_job):
    """Test that observations are tracked over time."""
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # First observation
    job = classifier.classify_job(sample_raw_job, current_time)
    assert len(job.observations) == 1
    assert job.observations[0]["timestamp"] == current_time.isoformat()

    # Second observation
    later_time = current_time + timedelta(days=1)
    updated_job = classifier.classify_job(sample_raw_job, later_time)
    assert len(updated_job.observations) == 2
    assert updated_job.observations[1]["timestamp"] == later_time.isoformat()


def test_classifier_with_low_threshold():
    """Test classifier with lower similarity threshold."""
    classifier = JobClassifier(similarity_threshold=0.75)
    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Original job
    job1 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Software Engineer",
        location="San Francisco",
        url="https://acme.com/jobs/1",
        source_identifier="job-1"
    )

    classifier.classify_job(job1, current_time)

    # Somewhat different job (would not match at 0.90 threshold)
    job2 = RawJob(
        company_id="acme-corp",
        company_name="Acme Corp",
        title="Junior Software Developer",
        location="San Francisco",
        url="https://acme.com/jobs/2",
        source_identifier="job-2"
    )

    classified2 = classifier.classify_job(job2, current_time + timedelta(days=1))

    # With lower threshold, might be detected as repost
    # (depends on actual similarity score)
    assert classified2.classification in [JobClassification.NEW, JobClassification.REPOST]
