"""
Test dataset with known repost scenarios for validation.

This module defines controlled test cases for validating repost detection
according to the revised PRD success criteria (≥90% accuracy in controlled cases).
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from src.ingestion.adapters.base import RawJob


class RepostTestScenario:
    """Represents a test scenario with expected classification."""

    def __init__(
        self,
        name: str,
        original_job: RawJob,
        test_job: RawJob,
        expected_is_repost: bool,
        description: str
    ):
        self.name = name
        self.original_job = original_job
        self.test_job = test_job
        self.expected_is_repost = expected_is_repost
        self.description = description


class RepostTestDataset:
    """
    Controlled test dataset for repost detection validation.

    Defines scenarios with known ground truth for measuring
    repost suppression effectiveness per PRD requirements.
    """

    @staticmethod
    def get_test_scenarios() -> List[RepostTestScenario]:
        """
        Generate test scenarios with known repost relationships.

        Returns:
            List of test scenarios with expected classifications
        """
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        scenarios = []

        # Scenario 1: Exact repost (same title, location, company)
        scenarios.append(RepostTestScenario(
            name="exact_repost",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Senior Software Engineer",
                location="San Francisco, CA",
                url="https://example.com/job/1",
                source_identifier="job-1"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Senior Software Engineer",
                location="San Francisco, CA",
                url="https://example.com/job/1-repost",
                source_identifier="job-1-repost"
            ),
            expected_is_repost=True,
            description="Identical job reposted with different URL/ID"
        ))

        # Scenario 2: Minor title variation (abbreviation)
        scenarios.append(RepostTestScenario(
            name="title_abbreviation",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Senior Software Engineer",
                location="San Francisco, CA",
                url="https://example.com/job/2",
                source_identifier="job-2"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Sr. Software Engineer",
                location="San Francisco, CA",
                url="https://example.com/job/2-repost",
                source_identifier="job-2-repost"
            ),
            expected_is_repost=True,
            description="Same job with abbreviated title (Senior -> Sr.)"
        ))

        # Scenario 3: Location format variation
        scenarios.append(RepostTestScenario(
            name="location_format",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Data Scientist",
                location="San Francisco, California",
                url="https://example.com/job/3",
                source_identifier="job-3"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Data Scientist",
                location="San Francisco, CA",
                url="https://example.com/job/3-repost",
                source_identifier="job-3-repost"
            ),
            expected_is_repost=True,
            description="Same job with state abbreviation (California -> CA)"
        ))

        # Scenario 4: Minor description change (NOT a repost)
        scenarios.append(RepostTestScenario(
            name="different_seniority",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Software Engineer",
                location="Remote",
                url="https://example.com/job/4",
                source_identifier="job-4"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Senior Software Engineer",
                location="Remote",
                url="https://example.com/job/4-different",
                source_identifier="job-4-different"
            ),
            expected_is_repost=False,
            description="Different seniority level - genuinely new role"
        ))

        # Scenario 5: Same title, different location (NOT a repost)
        scenarios.append(RepostTestScenario(
            name="different_location",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Product Manager",
                location="New York, NY",
                url="https://example.com/job/5",
                source_identifier="job-5"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Product Manager",
                location="San Francisco, CA",
                url="https://example.com/job/5-different",
                source_identifier="job-5-different"
            ),
            expected_is_repost=False,
            description="Same title, different location - separate opening"
        ))

        # Scenario 6: Punctuation differences
        scenarios.append(RepostTestScenario(
            name="punctuation_variation",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Machine Learning Engineer - Computer Vision",
                location="Seattle, WA",
                url="https://example.com/job/6",
                source_identifier="job-6"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Machine Learning Engineer (Computer Vision)",
                location="Seattle, WA",
                url="https://example.com/job/6-repost",
                source_identifier="job-6-repost"
            ),
            expected_is_repost=True,
            description="Same job with different punctuation (dash vs parentheses)"
        ))

        # Scenario 7: Remote vs specific location
        scenarios.append(RepostTestScenario(
            name="remote_to_location",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Backend Engineer",
                location="Remote",
                url="https://example.com/job/7",
                source_identifier="job-7"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Backend Engineer",
                location="Remote - US",
                url="https://example.com/job/7-repost",
                source_identifier="job-7-repost"
            ),
            expected_is_repost=True,
            description="Remote job with more specific location qualifier"
        ))

        # Scenario 8: Different role entirely
        scenarios.append(RepostTestScenario(
            name="completely_different",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Software Engineer",
                location="Boston, MA",
                url="https://example.com/job/8",
                source_identifier="job-8"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Marketing Manager",
                location="Boston, MA",
                url="https://example.com/job/8-different",
                source_identifier="job-8-different"
            ),
            expected_is_repost=False,
            description="Completely different role, same location"
        ))

        # Scenario 9: Multiple word order variation
        scenarios.append(RepostTestScenario(
            name="word_order",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Research Engineer - Machine Learning",
                location="Palo Alto, CA",
                url="https://example.com/job/9",
                source_identifier="job-9"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Machine Learning Research Engineer",
                location="Palo Alto, CA",
                url="https://example.com/job/9-repost",
                source_identifier="job-9-repost"
            ),
            expected_is_repost=True,
            description="Same role with reordered words"
        ))

        # Scenario 10: Specialization addition (borderline case)
        scenarios.append(RepostTestScenario(
            name="specialization_added",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Software Engineer",
                location="Austin, TX",
                url="https://example.com/job/10",
                source_identifier="job-10"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Software Engineer - Infrastructure",
                location="Austin, TX",
                url="https://example.com/job/10-different",
                source_identifier="job-10-different"
            ),
            expected_is_repost=False,
            description="General role vs specialized role - likely different"
        ))

        # Scenario 11: Same company, different entity
        scenarios.append(RepostTestScenario(
            name="different_company_entity",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo Inc",
                title="DevOps Engineer",
                location="Chicago, IL",
                url="https://example.com/job/11",
                source_identifier="job-11"
            ),
            test_job=RawJob(
                company_id="test-co-labs",
                company_name="TestCo Labs",
                title="DevOps Engineer",
                location="Chicago, IL",
                url="https://example.com/job/11-different",
                source_identifier="job-11-different"
            ),
            expected_is_repost=False,
            description="Different company ID despite similar name"
        ))

        # Scenario 12: Hybrid vs Remote
        scenarios.append(RepostTestScenario(
            name="hybrid_vs_remote",
            original_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Full Stack Engineer",
                location="Hybrid - Seattle, WA",
                url="https://example.com/job/12",
                source_identifier="job-12"
            ),
            test_job=RawJob(
                company_id="test-co",
                company_name="TestCo",
                title="Full Stack Engineer",
                location="Seattle, WA",
                url="https://example.com/job/12-different",
                source_identifier="job-12-different"
            ),
            expected_is_repost=False,
            description="Work arrangement difference matters (Hybrid vs In-office)"
        ))

        return scenarios

    @staticmethod
    def get_expected_metrics() -> Dict[str, float]:
        """
        Return expected performance metrics for this test dataset.

        According to revised PRD:
        - Repost suppression effectiveness: ≥90% in controlled test cases

        Returns:
            Dict with metric names and expected values
        """
        return {
            "min_repost_detection_rate": 0.90,  # At least 90% of reposts correctly identified
            "max_false_positive_rate": 0.20,    # Allow some false positives in borderline cases
            "total_scenarios": 12,
            "expected_reposts": 6,              # Scenarios marked expected_is_repost=True
            "expected_new": 6                   # Scenarios marked expected_is_repost=False
        }

    @staticmethod
    def get_borderline_scenarios() -> List[str]:
        """
        Return list of scenario names considered borderline/ambiguous.

        These scenarios may have legitimate disagreement in classification
        and should be documented rather than treated as failures.

        Returns:
            List of scenario names that are borderline cases
        """
        return [
            "specialization_added",      # General vs specialized role
            "hybrid_vs_remote",         # Work arrangement differences
            "remote_to_location"        # Remote scope clarification
        ]
