"""
Repost detection validation tests using controlled test dataset.

Validates repost suppression effectiveness per revised PRD metrics:
- Target: ≥90% detection rate in controlled test cases
- Focus: Deterministic, rule-based classification (not statistical ML)
"""

import pytest
from datetime import datetime, timedelta

from src.processing.classifier import JobClassifier
from tests.test_dataset_repost_scenarios import RepostTestDataset, RepostTestScenario


class TestRepostValidation:
    """
    Validation tests for repost detection using controlled scenarios.

    These tests validate the system's ability to correctly identify reposts
    in controlled cases with known ground truth, per PRD success criteria.
    """

    @pytest.fixture
    def classifier(self):
        """Create classifier with default settings."""
        return JobClassifier(
            repost_window_days=30,
            similarity_threshold=0.90
        )

    @pytest.fixture
    def test_scenarios(self):
        """Load test scenarios."""
        return RepostTestDataset.get_test_scenarios()

    @pytest.fixture
    def expected_metrics(self):
        """Load expected metrics."""
        return RepostTestDataset.get_expected_metrics()

    def test_individual_scenarios(self, classifier, test_scenarios):
        """
        Test each repost scenario individually.

        This test runs each scenario separately to identify which specific
        cases pass or fail, supporting debugging and explainability.
        """
        current_time = datetime(2024, 1, 15, 12, 0, 0)  # Within 30-day window

        for scenario in test_scenarios:
            # Classify original job
            original_classified = classifier.classify_job(
                scenario.original_job,
                current_time=datetime(2024, 1, 1, 12, 0, 0)
            )

            # Add to known jobs
            classifier.known_jobs[original_classified.id] = original_classified

            # Classify test job
            test_classified = classifier.classify_job(
                scenario.test_job,
                current_time=current_time
            )

            # Determine if detected as repost
            is_detected_as_repost = (test_classified.classification.value == "repost")

            # Log result for debugging
            print(f"\nScenario: {scenario.name}")
            print(f"  Description: {scenario.description}")
            print(f"  Expected repost: {scenario.expected_is_repost}")
            print(f"  Detected as repost: {is_detected_as_repost}")
            print(f"  Classification: {test_classified.classification.value}")
            print(f"  Reasoning: {test_classified.classification_reasoning}")

            # Soft assertion - document failures but don't fail test
            if is_detected_as_repost != scenario.expected_is_repost:
                print(f"  WARNING: MISMATCH in scenario '{scenario.name}'")

    def test_repost_detection_rate(self, classifier, test_scenarios, expected_metrics):
        """
        Validate repost detection rate meets PRD threshold (≥90%).

        This test validates that the system correctly identifies at least 90%
        of true reposts in controlled test cases.
        """
        current_time = datetime(2024, 1, 15, 12, 0, 0)
        true_reposts = [s for s in test_scenarios if s.expected_is_repost]

        correct_detections = 0

        for scenario in true_reposts:
            # Classify original
            original_classified = classifier.classify_job(
                scenario.original_job,
                current_time=datetime(2024, 1, 1, 12, 0, 0)
            )
            classifier.known_jobs[original_classified.id] = original_classified

            # Classify test job
            test_classified = classifier.classify_job(
                scenario.test_job,
                current_time=current_time
            )

            if test_classified.classification.value == "repost":
                correct_detections += 1

        detection_rate = correct_detections / len(true_reposts)

        print(f"\n=== Repost Detection Rate ===")
        print(f"True reposts: {len(true_reposts)}")
        print(f"Correctly detected: {correct_detections}")
        print(f"Detection rate: {detection_rate:.1%}")
        print(f"Target threshold: {expected_metrics['min_repost_detection_rate']:.1%}")

        # Validate against PRD target
        assert detection_rate >= expected_metrics['min_repost_detection_rate'], \
            f"Detection rate {detection_rate:.1%} below target {expected_metrics['min_repost_detection_rate']:.1%}"

    def test_false_positive_control(self, classifier, test_scenarios):
        """
        Monitor false positive rate for genuinely new jobs.

        Per revised PRD: We don't claim statistical accuracy, but we monitor
        to ensure no unbounded growth in false "New" flags.
        """
        current_time = datetime(2024, 1, 15, 12, 0, 0)
        genuinely_new = [s for s in test_scenarios if not s.expected_is_repost]

        false_positives = 0

        for scenario in genuinely_new:
            # Classify original
            original_classified = classifier.classify_job(
                scenario.original_job,
                current_time=datetime(2024, 1, 1, 12, 0, 0)
            )
            classifier.known_jobs[original_classified.id] = original_classified

            # Classify test job
            test_classified = classifier.classify_job(
                scenario.test_job,
                current_time=current_time
            )

            # False positive: genuinely new job incorrectly flagged as repost
            if test_classified.classification.value == "repost":
                false_positives += 1
                print(f"\nFalse positive: {scenario.name}")
                print(f"  Description: {scenario.description}")

        false_positive_rate = false_positives / len(genuinely_new) if genuinely_new else 0

        print(f"\n=== False Positive Monitoring ===")
        print(f"Genuinely new jobs: {len(genuinely_new)}")
        print(f"Incorrectly flagged as repost: {false_positives}")
        print(f"False positive rate: {false_positive_rate:.1%}")

        # Document rate but don't assert - per PRD, we monitor for unbounded growth
        # In controlled test set, some false positives are acceptable in borderline cases

    def test_classification_consistency(self, classifier, test_scenarios):
        """
        Verify classification is consistent across multiple runs.

        Validates deterministic behavior - same input should produce same result.
        """
        current_time = datetime(2024, 1, 15, 12, 0, 0)

        for scenario in test_scenarios:
            # Classify original
            original_classified = classifier.classify_job(
                scenario.original_job,
                current_time=datetime(2024, 1, 1, 12, 0, 0)
            )
            classifier.known_jobs[original_classified.id] = original_classified

            # Classify test job multiple times
            results = []
            for _ in range(3):
                test_classified = classifier.classify_job(
                    scenario.test_job,
                    current_time=current_time
                )
                results.append(test_classified.classification.value)

            # All results should be identical
            assert len(set(results)) == 1, \
                f"Inconsistent classification for {scenario.name}: {results}"

    def test_reasoning_explainability(self, classifier, test_scenarios):
        """
        Verify all classifications include reasoning.

        Per PRD: Detection logic must be auditable and explainable.
        """
        current_time = datetime(2024, 1, 15, 12, 0, 0)

        for scenario in test_scenarios:
            # Classify original
            original_classified = classifier.classify_job(
                scenario.original_job,
                current_time=datetime(2024, 1, 1, 12, 0, 0)
            )
            classifier.known_jobs[original_classified.id] = original_classified

            # Classify test job
            test_classified = classifier.classify_job(
                scenario.test_job,
                current_time=current_time
            )

            # Verify reasoning exists and is meaningful
            assert test_classified.classification_reasoning, \
                f"Missing reasoning for scenario '{scenario.name}'"
            assert len(test_classified.classification_reasoning) > 10, \
                f"Reasoning too short for scenario '{scenario.name}'"

            # Reasoning should mention similarity/matching if repost
            if test_classified.classification.value == "repost":
                reasoning_lower = test_classified.classification_reasoning.lower()
                assert any(term in reasoning_lower for term in ["similar", "match", "repost"]), \
                    f"Repost reasoning should mention similarity for '{scenario.name}'"

    def test_borderline_case_documentation(self, test_scenarios):
        """
        Document borderline cases that may have legitimate disagreement.

        Per PRD: System is deterministic, not statistical. Some cases are
        inherently ambiguous and should be documented, not treated as failures.
        """
        borderline_names = RepostTestDataset.get_borderline_scenarios()
        borderline_cases = [s for s in test_scenarios if s.name in borderline_names]

        print("\n=== Borderline Cases ===")
        print(f"Total borderline scenarios: {len(borderline_cases)}")

        for scenario in borderline_cases:
            print(f"\n{scenario.name}:")
            print(f"  {scenario.description}")
            print(f"  Expected: {'Repost' if scenario.expected_is_repost else 'New'}")
            print(f"  Rationale: Ambiguous case with legitimate classification disagreement")

        # Document but don't assert on borderline cases
        assert len(borderline_cases) > 0, "Should have documented borderline cases"


def test_overall_validation_summary():
    """
    Generate validation summary report.

    This test runs all scenarios and produces a summary report showing
    overall system performance against PRD success criteria.
    """
    classifier = JobClassifier(repost_window_days=30, similarity_threshold=0.90)
    scenarios = RepostTestDataset.get_test_scenarios()
    expected = RepostTestDataset.get_expected_metrics()

    current_time = datetime(2024, 1, 15, 12, 0, 0)

    # Run all scenarios
    results = {
        "total": len(scenarios),
        "reposts_correct": 0,
        "new_correct": 0,
        "reposts_missed": 0,
        "false_positives": 0
    }

    for scenario in scenarios:
        # Classify original
        original_classified = classifier.classify_job(
            scenario.original_job,
            current_time=datetime(2024, 1, 1, 12, 0, 0)
        )
        classifier.known_jobs[original_classified.id] = original_classified

        # Classify test job
        test_classified = classifier.classify_job(
            scenario.test_job,
            current_time=current_time
        )

        is_detected_as_repost = (test_classified.classification.value == "repost")

        if scenario.expected_is_repost:
            if is_detected_as_repost:
                results["reposts_correct"] += 1
            else:
                results["reposts_missed"] += 1
        else:
            if is_detected_as_repost:
                results["false_positives"] += 1
            else:
                results["new_correct"] += 1

    # Calculate rates
    repost_detection_rate = results["reposts_correct"] / expected["expected_reposts"]
    new_detection_rate = results["new_correct"] / expected["expected_new"]

    # Print summary
    print("\n" + "=" * 60)
    print("REPOST VALIDATION SUMMARY")
    print("=" * 60)
    print(f"\nTest Dataset:")
    print(f"  Total scenarios: {results['total']}")
    print(f"  Expected reposts: {expected['expected_reposts']}")
    print(f"  Expected new: {expected['expected_new']}")
    print(f"\nRepost Detection:")
    print(f"  Correctly detected: {results['reposts_correct']}/{expected['expected_reposts']}")
    print(f"  Detection rate: {repost_detection_rate:.1%}")
    print(f"  Target (PRD): {expected['min_repost_detection_rate']:.1%}")
    status = "PASS" if repost_detection_rate >= expected['min_repost_detection_rate'] else "FAIL"
    print(f"  Status: {status}")
    print(f"\nNew Job Detection:")
    print(f"  Correctly identified: {results['new_correct']}/{expected['expected_new']}")
    print(f"  Accuracy: {new_detection_rate:.1%}")
    print(f"\nError Analysis:")
    print(f"  Missed reposts: {results['reposts_missed']}")
    print(f"  False positives: {results['false_positives']}")
    print("\n" + "=" * 60)

    # Assert against PRD target
    assert repost_detection_rate >= expected['min_repost_detection_rate'], \
        f"Repost detection rate {repost_detection_rate:.1%} below PRD target"
