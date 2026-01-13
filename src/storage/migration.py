"""
Schema migration utilities for data format changes.

Supports migrating job data between schema versions.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Callable

from src.utils.logging import get_logger


class SchemaMigrator:
    """
    Handles schema migrations for job data.

    Supports versioned migrations with backup/restore.
    """

    def __init__(self, data_dir: str = "data/jobs"):
        """
        Initialize migrator.

        Args:
            data_dir: Job data directory
        """
        self.data_dir = Path(data_dir)
        self.logger = get_logger(__name__)

        # Migration registry: maps (from_version, to_version) -> migration function
        self.migrations: Dict[tuple, Callable] = {}
        self._register_migrations()

    def _register_migrations(self) -> None:
        """Register all available migrations."""
        # Example: self.migrations[("1.0.0", "1.1.0")] = self._migrate_1_0_to_1_1
        pass

    def migrate(self, from_version: str, to_version: str, backup: bool = True) -> bool:
        """
        Migrate data from one schema version to another.

        Args:
            from_version: Source schema version
            to_version: Target schema version
            backup: Whether to create backup before migration

        Returns:
            True if successful, False otherwise
        """
        source_file = self.data_dir / f"jobs-v{from_version.split('.')[0]}.json"

        if not source_file.exists():
            self.logger.error(f"Source file not found: {source_file}")
            return False

        # Create backup
        if backup:
            backup_file = source_file.with_suffix(f".backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json")
            shutil.copy2(source_file, backup_file)
            self.logger.info(f"Created backup: {backup_file}")

        # Load source data
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            file_version = data.get("version", "unknown")
            if file_version != from_version:
                self.logger.warning(
                    f"Version mismatch: file={file_version}, expected={from_version}"
                )

            # Find migration path
            migration_key = (from_version, to_version)
            if migration_key not in self.migrations:
                self.logger.error(
                    f"No migration available from {from_version} to {to_version}"
                )
                return False

            # Execute migration
            self.logger.info(f"Migrating from {from_version} to {to_version}")
            migration_func = self.migrations[migration_key]
            migrated_data = migration_func(data)

            # Update version
            migrated_data["version"] = to_version

            # Write migrated data
            target_file = self.data_dir / f"jobs-v{to_version.split('.')[0]}.json"
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(migrated_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Migration complete: {target_file}")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            return False

    def validate_migration(self, file_path: Path, expected_version: str) -> bool:
        """
        Validate that migrated data matches expected schema.

        Args:
            file_path: Path to migrated data file
            expected_version: Expected schema version

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("version") != expected_version:
                self.logger.error(
                    f"Version mismatch: {data.get('version')} != {expected_version}"
                )
                return False

            # Additional validation could use jsonschema here
            return True

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False
