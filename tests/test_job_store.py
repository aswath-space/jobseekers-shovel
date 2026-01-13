"""
Tests for job storage functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.storage.job_store import JobStore
from src.processing.classifier import ClassifiedJob, JobClassification, JobStatus


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_job():
    """Create sample classified job."""
    return ClassifiedJob(
        id="test-job-1",
        company_id="test-company",
        company_name="Test Company",
        title="Software Engineer",
        location="San Francisco, CA",
        url="https://example.com/job/1",
        signature="test-company|software engineer|san francisco california",
        classification=JobClassification.NEW,
        classification_reasoning="Test job",
        status=JobStatus.ACTIVE,
        first_seen=datetime(2024, 1, 15, 12, 0, 0),
        last_seen=datetime(2024, 1, 15, 12, 0, 0),
        observations=[{
            "timestamp": "2024-01-15T12:00:00",
            "source_identifier": "job-1",
            "url": "https://example.com/job/1"
        }],
        source_identifier="job-1",
        department="Engineering",
        description="Test description",
        created_at=datetime(2024, 1, 15, 12, 0, 0),
        updated_at=datetime(2024, 1, 15, 12, 0, 0)
    )


def test_job_store_initialization(temp_dir):
    """Test job store initialization."""
    store = JobStore(data_dir=temp_dir)
    assert store.data_dir == Path(temp_dir)
    assert store.schema_version == "1.0.0"
    assert store.file_path.exists() is False


def test_load_jobs_empty(temp_dir):
    """Test loading from non-existent file."""
    store = JobStore(data_dir=temp_dir)
    jobs = store.load_jobs()
    assert len(jobs) == 0


def test_save_and_load_jobs(temp_dir, sample_job):
    """Test saving and loading jobs."""
    store = JobStore(data_dir=temp_dir)

    jobs = {sample_job.id: sample_job}
    success = store.save_jobs(jobs)
    assert success is True
    assert store.file_path.exists()

    loaded = store.load_jobs()
    assert len(loaded) == 1
    assert sample_job.id in loaded

    loaded_job = loaded[sample_job.id]
    assert loaded_job.title == sample_job.title
    assert loaded_job.company_name == sample_job.company_name
    assert loaded_job.status == sample_job.status


def test_save_multiple_jobs(temp_dir):
    """Test saving multiple jobs."""
    store = JobStore(data_dir=temp_dir)

    jobs = {}
    for i in range(5):
        job = ClassifiedJob(
            id=f"job-{i}",
            company_id="test",
            company_name="Test",
            title=f"Job {i}",
            location="Remote",
            url=f"https://example.com/{i}",
            signature=f"test|job {i}|remote",
            classification=JobClassification.NEW,
            classification_reasoning="Test",
            status=JobStatus.ACTIVE,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            observations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        jobs[job.id] = job

    store.save_jobs(jobs)
    loaded = store.load_jobs()
    assert len(loaded) == 5


def test_export_to_csv(temp_dir, sample_job):
    """Test CSV export."""
    store = JobStore(data_dir=temp_dir)
    jobs = {sample_job.id: sample_job}

    csv_path = Path(temp_dir) / "export.csv"
    success = store.export_to_csv(str(csv_path), jobs)
    assert success is True
    assert csv_path.exists()

    # Check CSV content
    content = csv_path.read_text()
    assert "Software Engineer" in content
    assert "Test Company" in content


def test_json_structure(temp_dir, sample_job):
    """Test JSON file structure."""
    store = JobStore(data_dir=temp_dir)
    jobs = {sample_job.id: sample_job}
    store.save_jobs(jobs)

    with open(store.file_path) as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert "generated_at" in data
    assert data["job_count"] == 1
    assert len(data["jobs"]) == 1

    job_data = data["jobs"][0]
    assert job_data["id"] == sample_job.id
    assert job_data["classification"] == "new"
    assert job_data["status"] == "active"
