"""
Tests for artifact versioning functionality.
"""

import json
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from src.storage.versioning import ArtifactVersionManager


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as data_dir:
        with tempfile.TemporaryDirectory() as versions_dir:
            yield data_dir, versions_dir


@pytest.fixture
def sample_data():
    """Create sample job data."""
    return {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "job_count": 5,
        "jobs": []
    }


def test_version_manager_initialization(temp_dirs):
    """Test version manager initialization."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    assert manager.data_dir == Path(data_dir)
    assert manager.versions_dir == Path(versions_dir)
    assert manager.max_versions == 30
    assert manager.versions_dir.exists()


def test_create_snapshot(temp_dirs, sample_data):
    """Test creating a snapshot."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    # Create source file
    source_path = Path(data_dir) / "jobs-v1.json"
    with open(source_path, 'w') as f:
        json.dump(sample_data, f)

    snapshot_path = manager.create_snapshot()
    assert snapshot_path is not None
    assert Path(snapshot_path).exists()
    assert "jobs-v1-" in snapshot_path


def test_create_snapshot_nonexistent_source(temp_dirs):
    """Test creating snapshot when source doesn't exist."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    snapshot_path = manager.create_snapshot()
    assert snapshot_path is None


def test_list_snapshots(temp_dirs, sample_data):
    """Test listing snapshots."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    # Create source file
    source_path = Path(data_dir) / "jobs-v1.json"
    with open(source_path, 'w') as f:
        json.dump(sample_data, f)

    # Create multiple snapshots
    manager.create_snapshot()
    time.sleep(0.1)
    manager.create_snapshot()
    time.sleep(0.1)
    manager.create_snapshot()

    snapshots = manager.list_snapshots()
    assert len(snapshots) == 3
    assert all('path' in s for s in snapshots)
    assert all('timestamp' in s for s in snapshots)
    assert all('size_bytes' in s for s in snapshots)

    # Check sorted by timestamp descending
    timestamps = [s['timestamp'] for s in snapshots]
    assert timestamps == sorted(timestamps, reverse=True)


def test_rotate_versions(temp_dirs, sample_data):
    """Test version rotation."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir, max_versions=3)

    # Create source file
    source_path = Path(data_dir) / "jobs-v1.json"
    with open(source_path, 'w') as f:
        json.dump(sample_data, f)

    # Create 5 snapshots
    for _ in range(5):
        manager.create_snapshot()
        time.sleep(0.1)

    assert len(manager.list_snapshots()) == 5

    # Rotate - should keep only 3 most recent
    deleted = manager.rotate_versions()
    assert deleted == 2
    assert len(manager.list_snapshots()) == 3


def test_restore_snapshot(temp_dirs, sample_data):
    """Test restoring a snapshot."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    # Create source file
    source_path = Path(data_dir) / "jobs-v1.json"
    with open(source_path, 'w') as f:
        json.dump(sample_data, f)

    # Create snapshot
    snapshot_path = manager.create_snapshot()
    snapshot_name = Path(snapshot_path).name

    # Modify source
    modified_data = sample_data.copy()
    modified_data["job_count"] = 10
    with open(source_path, 'w') as f:
        json.dump(modified_data, f)

    # Restore snapshot
    success = manager.restore_snapshot(snapshot_name)
    assert success is True

    # Verify restored data
    with open(source_path) as f:
        restored_data = json.load(f)
    assert restored_data["job_count"] == 5


def test_restore_nonexistent_snapshot(temp_dirs):
    """Test restoring a nonexistent snapshot."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    success = manager.restore_snapshot("nonexistent-snapshot.json")
    assert success is False


def test_get_snapshot_info(temp_dirs, sample_data):
    """Test getting snapshot information."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    # Create source file
    source_path = Path(data_dir) / "jobs-v1.json"
    with open(source_path, 'w') as f:
        json.dump(sample_data, f)

    # Create snapshot
    snapshot_path = manager.create_snapshot()
    snapshot_name = Path(snapshot_path).name

    info = manager.get_snapshot_info(snapshot_name)
    assert info is not None
    assert info["version"] == "1.0.0"
    assert info["job_count"] == 5
    assert "timestamp" in info


def test_cleanup_corrupted_snapshots(temp_dirs):
    """Test cleaning up corrupted snapshots."""
    data_dir, versions_dir = temp_dirs
    manager = ArtifactVersionManager(data_dir, versions_dir)

    # Create valid snapshot
    valid_path = Path(versions_dir) / "jobs-v1-20240101-120000.json"
    with open(valid_path, 'w') as f:
        json.dump({"version": "1.0.0", "jobs": []}, f)

    # Create corrupted snapshot
    corrupted_path = Path(versions_dir) / "jobs-v1-20240102-120000.json"
    with open(corrupted_path, 'w') as f:
        f.write("invalid json{")

    cleaned = manager.cleanup_corrupted_snapshots()
    assert cleaned == 1
    assert valid_path.exists()
    assert not corrupted_path.exists()
