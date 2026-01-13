"""
Ingestion orchestrator - coordinates job fetching across all companies.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.utils.config import get_config, ConfigurationError
from src.utils.logging import setup_logging, get_logger
from src.ingestion.crawler import create_crawler_from_config
from src.ingestion.adapters.base import create_adapter, AdapterError
from src.processing.classifier import JobClassifier
from src.storage.job_store import JobStore
from src.storage.versioning import ArtifactVersionManager


class IngestionOrchestrator:
    """
    Orchestrates job ingestion across all configured companies.

    Responsibilities:
    - Load configuration
    - Initialize adapters for each company
    - Coordinate ingestion execution
    - Handle errors gracefully
    - Report results
    """

    def __init__(self, config_dir: str = "config", data_dir: str = "data/jobs"):
        """
        Initialize orchestrator.

        Args:
            config_dir: Directory containing configuration files
            data_dir: Directory for job data storage
        """
        self.config = get_config(config_dir)
        self.logger = get_logger(__name__)
        self.results: List[Dict[str, Any]] = []
        self.crawler = None

        # Initialize job store, version manager, and classifier
        self.job_store = JobStore(data_dir=data_dir)
        self.version_manager = ArtifactVersionManager(data_dir=data_dir)

        # Load classification config from ingestion.yml
        ingestion_config = self.config.load_ingestion_config()
        classification_config = ingestion_config.get("classification", {})

        self.classifier = JobClassifier(
            repost_window_days=classification_config.get("repost_window_days", 30),
            similarity_threshold=classification_config.get("similarity_threshold", 0.90)
        )

    def run(self) -> Dict[str, Any]:
        """
        Execute ingestion for all configured companies.

        Returns:
            Dictionary containing:
                - success: bool
                - companies_processed: int
                - companies_succeeded: int
                - companies_failed: int
                - results: List of per-company results
                - timestamp: Ingestion start timestamp
        """
        start_time = datetime.utcnow()
        self.logger.info("=" * 60)
        self.logger.info("Starting job ingestion")
        self.logger.info(f"Timestamp: {start_time.isoformat()}")
        self.logger.info("=" * 60)

        try:
            companies = self.config.load_companies()
        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": start_time.isoformat(),
            }

        self.logger.info(f"Loaded {len(companies)} companies from configuration")

        # Load existing jobs into classifier
        existing_jobs = self.job_store.load_jobs()
        self.classifier.known_jobs = existing_jobs
        self.logger.info(f"Loaded {len(existing_jobs)} existing jobs from storage")

        # Initialize crawler with config
        ingestion_config = self.config.load_ingestion_config()
        self.crawler = create_crawler_from_config(ingestion_config)
        self.logger.debug("Initialized HTTP crawler with rate limiting")

        results = []
        succeeded = 0
        failed = 0
        all_observed_job_ids = []

        for company in companies:
            company_id = company["id"]
            company_name = company["name"]

            self.logger.info("-" * 60)
            self.logger.info(f"Processing: {company_name} ({company_id})")

            try:
                result = self._process_company(company, start_time)
                if result["success"]:
                    succeeded += 1
                    # Track observed job IDs for lifecycle management
                    all_observed_job_ids.extend(result.get("observed_job_ids", []))
                    self.logger.info(
                        f"SUCCESS: {company_name}: "
                        f"Classified {result.get('jobs_classified', 0)} jobs "
                        f"(new={result.get('new_jobs', 0)}, "
                        f"repost={result.get('repost_jobs', 0)}, "
                        f"existing={result.get('existing_jobs', 0)})"
                    )
                else:
                    failed += 1
                    self.logger.error(
                        f"FAILED: {company_name}: {result.get('error', 'Unknown error')}"
                    )
                results.append(result)
            except Exception as e:
                failed += 1
                error_msg = f"Unexpected error: {e}"
                self.logger.error(f"FAILED: {company_name}: {error_msg}", exc_info=True)
                results.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "success": False,
                    "error": error_msg,
                })

        # Clean up crawler
        if self.crawler:
            self.crawler.close()

        # Lifecycle management: mark jobs that weren't observed
        missing_count = self.classifier.mark_missing_jobs(all_observed_job_ids, start_time)
        if missing_count > 0:
            self.logger.info(f"Marked {missing_count} jobs as missing (not observed in this cycle)")

        # Close jobs that have been missing too long
        close_timeout_days = ingestion_config.get("classification", {}).get("close_timeout_days", 14)
        closed_count = self.classifier.close_old_missing_jobs(close_timeout_days, start_time)
        if closed_count > 0:
            self.logger.info(f"Closed {closed_count} jobs (missing for > {close_timeout_days} days)")

        # Save updated job data with versioning
        save_success = self.job_store.save_jobs(self.classifier.known_jobs)
        if save_success:
            self.logger.info(f"Saved {len(self.classifier.known_jobs)} jobs to storage")

            # Create snapshot and rotate versions
            snapshot_path = self.version_manager.create_snapshot()
            if snapshot_path:
                self.logger.info(f"Created snapshot: {Path(snapshot_path).name}")

            deleted = self.version_manager.rotate_versions()
            if deleted > 0:
                self.logger.info(f"Rotated versions: deleted {deleted} old snapshots")
        else:
            self.logger.error("Failed to save jobs to storage")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        self.logger.info("=" * 60)
        self.logger.info("Ingestion complete")
        self.logger.info(f"Total companies: {len(companies)}")
        self.logger.info(f"Succeeded: {succeeded}")
        self.logger.info(f"Failed: {failed}")
        self.logger.info(f"Total jobs in database: {len(self.classifier.known_jobs)}")
        self.logger.info(f"Duration: {duration:.2f} seconds")
        self.logger.info("=" * 60)

        return {
            "success": True,
            "companies_processed": len(companies),
            "companies_succeeded": succeeded,
            "companies_failed": failed,
            "results": results,
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration,
        }

    def _process_company(self, company: Dict[str, Any], current_time: datetime) -> Dict[str, Any]:
        """
        Process a single company.

        Args:
            company: Company configuration dictionary
            current_time: Current timestamp for classification

        Returns:
            Result dictionary with success status and details
        """
        company_id = company["id"]
        company_name = company["name"]
        adapter_type = company["adapter"]
        sources = company["sources"]

        self.logger.debug(f"Adapter type: {adapter_type}")

        try:
            # Create adapter
            adapter = create_adapter(adapter_type, company_id, company_name)
            self.logger.debug(f"Created {adapter_type} adapter")

            # Fetch jobs from all sources
            all_raw_jobs = []
            for source in sources:
                source_url = source["url"]
                self.logger.debug(f"Fetching from: {source_url}")

                try:
                    jobs = adapter.fetch_jobs(source_url, self.crawler)
                    all_raw_jobs.extend(jobs)
                    self.logger.debug(f"Fetched {len(jobs)} jobs from {source_url}")

                except AdapterError as e:
                    self.logger.error(f"Adapter error for {source_url}: {e}")
                    # Continue with other sources even if one fails
                    continue

            # Classify all fetched jobs
            classified_job_ids = []
            classification_counts = {"new": 0, "repost": 0, "existing": 0}

            for raw_job in all_raw_jobs:
                try:
                    classified_job = self.classifier.classify_job(raw_job, current_time)
                    classified_job_ids.append(classified_job.id)

                    # Track classification type
                    classification_type = classified_job.classification.value
                    if classification_type in classification_counts:
                        classification_counts[classification_type] += 1

                except Exception as e:
                    self.logger.error(f"Error classifying job: {e}", exc_info=True)
                    continue

            return {
                "company_id": company_id,
                "company_name": company_name,
                "adapter": adapter_type,
                "success": True,
                "jobs_fetched": len(all_raw_jobs),
                "jobs_classified": len(classified_job_ids),
                "new_jobs": classification_counts["new"],
                "repost_jobs": classification_counts["repost"],
                "existing_jobs": classification_counts["existing"],
                "observed_job_ids": classified_job_ids,
                "sources_processed": len(sources),
            }

        except ValueError as e:
            # Unknown adapter type
            return {
                "company_id": company_id,
                "company_name": company_name,
                "adapter": adapter_type,
                "success": False,
                "error": str(e),
            }

        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected error processing {company_name}: {e}", exc_info=True)
            return {
                "company_id": company_id,
                "company_name": company_name,
                "adapter": adapter_type,
                "success": False,
                "error": f"Unexpected error: {e}",
            }


def main():
    """Command-line entry point for ingestion."""
    parser = argparse.ArgumentParser(
        description="Job ingestion orchestrator for JobSeekers Shovel"
    )
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory (default: config)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional log file path",
    )

    args = parser.parse_args()

    # Setup logging
    try:
        config = get_config(args.config_dir)
        ingestion_config = config.load_ingestion_config()

        # Get logging config from file or use command-line args
        log_config = ingestion_config.get("logging", {})
        log_level = args.log_level or log_config.get("level", "INFO")
        log_format = log_config.get("format")
        log_file = args.log_file

        if log_file is None and log_config.get("file_enabled", False):
            log_file = log_config.get("file_path", "logs/ingestion.log")

        setup_logging(level=log_level, log_format=log_format, log_file=log_file)
        logger = get_logger(__name__)

    except Exception as e:
        print(f"Failed to setup logging: {e}", file=sys.stderr)
        sys.exit(1)

    # Run orchestrator
    try:
        orchestrator = IngestionOrchestrator(config_dir=args.config_dir)
        result = orchestrator.run()

        if not result.get("success", False):
            logger.error("Ingestion failed")
            sys.exit(1)

        if result.get("companies_failed", 0) > 0:
            logger.warning(
                f"Ingestion completed with {result['companies_failed']} failures"
            )
            sys.exit(2)

        logger.info("Ingestion completed successfully")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
