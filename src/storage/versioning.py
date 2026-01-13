"""
Artifact versioning and storage strategy.

Manages versioned storage of job data artifacts with rotation and archival.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ArtifactVersionManager:
    """Manages versioned storage of job data artifacts."""

    def __init__(
        self,
        data_dir: str = "data/jobs",
        versions_dir: str = "data/versions",
        max_versions: int = 30
    ):
        """
        Initialize artifact version manager.

        Args:
            data_dir: Directory containing current job data
            versions_dir: Directory for versioned snapshots
            max_versions: Maximum number of versions to retain (default: 30 days)
        """
        self.data_dir = Path(data_dir)
        self.versions_dir = Path(versions_dir)
        self.max_versions = max_versions
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, source_file: str = "jobs-v1.json") -> Optional[str]:
        """
        Create timestamped snapshot of current data artifact.

        Args:
            source_file: Name of source file to snapshot

        Returns:
            Path to created snapshot, or None if source doesn't exist
        """
        source_path = self.data_dir / source_file
        if not source_path.exists():
            return None

        # Create timestamped snapshot with microsecond precision
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        snapshot_name = f"jobs-v1-{timestamp}.json"
        snapshot_path = self.versions_dir / snapshot_name

        shutil.copy2(source_path, snapshot_path)
        return str(snapshot_path)

    def list_snapshots(self) -> List[Dict[str, any]]:
        """
        List all available snapshots with metadata.

        Returns:
            List of snapshot metadata dicts with keys: path, timestamp, size
        """
        snapshots = []
        for snapshot_path in sorted(self.versions_dir.glob("jobs-v1-*.json")):
            stat = snapshot_path.stat()
            snapshots.append({
                "path": str(snapshot_path),
                "name": snapshot_path.name,
                "timestamp": datetime.fromtimestamp(stat.st_mtime),
                "size_bytes": stat.st_size
            })

        return sorted(snapshots, key=lambda s: s["timestamp"], reverse=True)

    def rotate_versions(self) -> int:
        """
        Remove old versions beyond retention limit.

        Keeps most recent max_versions snapshots.

        Returns:
            Number of versions deleted
        """
        snapshots = self.list_snapshots()

        if len(snapshots) <= self.max_versions:
            return 0

        # Delete oldest versions beyond limit
        to_delete = snapshots[self.max_versions:]
        deleted = 0

        for snapshot in to_delete:
            Path(snapshot["path"]).unlink()
            deleted += 1

        return deleted

    def restore_snapshot(self, snapshot_name: str, target_file: str = "jobs-v1.json") -> bool:
        """
        Restore a snapshot to current data file.

        Args:
            snapshot_name: Name of snapshot to restore
            target_file: Target file name in data_dir

        Returns:
            True if restore succeeded, False otherwise
        """
        snapshot_path = self.versions_dir / snapshot_name
        if not snapshot_path.exists():
            return False

        target_path = self.data_dir / target_file

        # Backup current file before restore
        if target_path.exists():
            backup_name = f"{target_file}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            shutil.copy2(target_path, self.data_dir / backup_name)

        shutil.copy2(snapshot_path, target_path)
        return True

    def get_snapshot_info(self, snapshot_name: str) -> Optional[Dict]:
        """
        Get detailed information about a snapshot.

        Args:
            snapshot_name: Name of snapshot

        Returns:
            Dict with snapshot metadata including job count, version, etc.
        """
        snapshot_path = self.versions_dir / snapshot_name
        if not snapshot_path.exists():
            return None

        try:
            with open(snapshot_path) as f:
                data = json.load(f)

            stat = snapshot_path.stat()

            return {
                "name": snapshot_name,
                "path": str(snapshot_path),
                "timestamp": datetime.fromtimestamp(stat.st_mtime),
                "size_bytes": stat.st_size,
                "version": data.get("version", "unknown"),
                "job_count": data.get("job_count", 0),
                "generated_at": data.get("generated_at", "unknown")
            }
        except (json.JSONDecodeError, KeyError):
            return None

    def cleanup_corrupted_snapshots(self) -> int:
        """
        Remove snapshots that cannot be parsed as valid JSON.

        Returns:
            Number of corrupted snapshots removed
        """
        cleaned = 0

        for snapshot_path in self.versions_dir.glob("jobs-v1-*.json"):
            try:
                with open(snapshot_path) as f:
                    json.load(f)
            except json.JSONDecodeError:
                snapshot_path.unlink()
                cleaned += 1

        return cleaned
