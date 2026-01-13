"""
Tests for job signature normalization.
"""

import pytest

from src.processing.normalizer import JobNormalizer


def test_normalize_title_basic():
    """Test basic title normalization."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_title("Software Engineer") == "software engineer"
    assert normalizer.normalize_title("SENIOR ENGINEER") == "senior engineer"
    assert normalizer.normalize_title("  Multiple   Spaces  ") == "multiple spaces"


def test_normalize_title_abbreviations():
    """Test title abbreviation expansion."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_title("Sr. Software Engineer") == "senior software engineer"
    assert normalizer.normalize_title("Jr Developer") == "junior developer"
    assert normalizer.normalize_title("DevOps Engineer") == "development operations engineer"
    assert normalizer.normalize_title("QA Engineer") == "quality assurance engineer"
    assert normalizer.normalize_title("UI/UX Designer") == "user interface user experience designer"


def test_normalize_title_punctuation():
    """Test punctuation handling in titles."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_title("Engineer - Backend") == "engineer backend"
    assert normalizer.normalize_title("Engineer, Senior") == "engineer senior"
    assert normalizer.normalize_title("C++ Developer") == "c developer"


def test_normalize_location_basic():
    """Test basic location normalization."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_location("San Francisco") == "san francisco"
    assert normalizer.normalize_location("NEW YORK") == "new york"
    assert normalizer.normalize_location("  Boston  ") == "boston"


def test_normalize_location_abbreviations():
    """Test location abbreviation expansion."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_location("San Francisco, CA") == "san francisco california"
    assert normalizer.normalize_location("New York, NY") == "new york new york"
    assert normalizer.normalize_location("Austin, TX") == "austin texas"
    assert normalizer.normalize_location("SF") == "san francisco"
    assert normalizer.normalize_location("NYC") == "new york city"


def test_normalize_location_remote():
    """Test remote location normalization."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_location("Remote") == "remote"
    assert normalizer.normalize_location("Remote - US") == "remote"
    assert normalizer.normalize_location("Remote (US)") == "remote"
    assert normalizer.normalize_location("Work from Home") == "remote"
    assert normalizer.normalize_location("WFH") == "remote"


def test_normalize_location_empty():
    """Test empty location handling."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_location("") == "unknown"
    assert normalizer.normalize_location(None) == "unknown"


def test_create_signature():
    """Test signature creation."""
    normalizer = JobNormalizer()

    signature = normalizer.create_signature(
        company_id="acme-corp",
        title="Sr. Software Engineer",
        location="San Francisco, CA"
    )

    assert signature == "acme-corp|senior software engineer|san francisco california"


def test_create_signature_consistency():
    """Test that similar jobs create same signature."""
    normalizer = JobNormalizer()

    sig1 = normalizer.create_signature(
        "company-1", "Senior Software Engineer", "San Francisco, CA"
    )

    sig2 = normalizer.create_signature(
        "company-1", "Sr. Software Engineer", "San Francisco, California"
    )

    sig3 = normalizer.create_signature(
        "company-1", "SENIOR  SOFTWARE  ENGINEER", "SF, CA"
    )

    # All should be similar (note: "california" vs full state name differs)
    assert sig1 == "company-1|senior software engineer|san francisco california"
    assert sig2 == "company-1|senior software engineer|san francisco california"
    assert sig3 == "company-1|senior software engineer|san francisco california"


def test_get_normalization_details():
    """Test getting normalization details for explainability."""
    normalizer = JobNormalizer()

    details = normalizer.get_normalization_details(
        title="Sr. DevOps Engineer",
        location="NYC"
    )

    assert details["original_title"] == "Sr. DevOps Engineer"
    assert details["normalized_title"] == "senior development operations engineer"
    assert details["original_location"] == "NYC"
    assert details["normalized_location"] == "new york city"


def test_title_edge_cases():
    """Test edge cases in title normalization."""
    normalizer = JobNormalizer()

    assert normalizer.normalize_title("") == ""
    assert normalizer.normalize_title("Engineer/Developer") == "engineer developer"
    assert normalizer.normalize_title("Sr./Jr. Engineer") == "senior junior engineer"
