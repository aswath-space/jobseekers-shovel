"""
Job signature normalization logic.

Normalizes job titles and locations for consistent matching and comparison.
"""

import re
from typing import Dict

from src.utils.logging import get_logger


class JobNormalizer:
    """
    Normalizes job data for signature matching.

    Handles case folding, whitespace, abbreviations, and location parsing
    to enable reliable matching across job postings.
    """

    # Common title abbreviations and their expansions
    TITLE_ABBREVIATIONS = {
        "sr": "senior",
        "sr.": "senior",
        "jr": "junior",
        "jr.": "junior",
        "mgr": "manager",
        "mgr.": "manager",
        "eng": "engineer",
        "engr": "engineer",
        "engr.": "engineer",
        "dev": "developer",
        "devops": "development operations",
        "sre": "site reliability engineer",
        "qa": "quality assurance",
        "ui": "user interface",
        "ux": "user experience",
        "vp": "vice president",
        "cto": "chief technology officer",
        "ceo": "chief executive officer",
        "cfo": "chief financial officer",
        "coo": "chief operating officer",
        "svp": "senior vice president",
        "evp": "executive vice president",
        "assoc": "associate",
        "asst": "assistant",
        "dir": "director",
        "dir.": "director",
        "admin": "administrator",
        "coord": "coordinator",
        "coord.": "coordinator",
        "acct": "account",
        "dept": "department",
        "ops": "operations",
        "spec": "specialist",
    }

    # Location normalizations
    LOCATION_NORMALIZATIONS = {
        "sf": "san francisco",
        "ny": "new york",
        "nyc": "new york city",
        "la": "los angeles",
        "dc": "washington dc",
        "remote us": "remote",
        "remote - us": "remote",
        "remote (us)": "remote",
        "work from home": "remote",
        "wfh": "remote",
    }

    # US state abbreviations
    STATE_ABBREVIATIONS = {
        "ca": "california",
        "ny": "new york",
        "tx": "texas",
        "fl": "florida",
        "il": "illinois",
        "ma": "massachusetts",
        "wa": "washington",
        "pa": "pennsylvania",
        "oh": "ohio",
        "ga": "georgia",
        "nc": "north carolina",
        "mi": "michigan",
        "nj": "new jersey",
        "va": "virginia",
        "az": "arizona",
        "co": "colorado",
        "or": "oregon",
        "md": "maryland",
        "tn": "tennessee",
        "in": "indiana",
    }

    def __init__(self):
        """Initialize normalizer."""
        self.logger = get_logger(__name__)

    def normalize_title(self, title: str) -> str:
        """
        Normalize job title for matching.

        Steps:
        1. Convert to lowercase
        2. Expand abbreviations
        3. Remove extra whitespace
        4. Strip punctuation
        5. Normalize common patterns

        Args:
            title: Raw job title

        Returns:
            Normalized title string

        Examples:
            "Sr. Software Engineer" -> "senior software engineer"
            "DevOps  Engineer" -> "development operations engineer"
            "QA Engineer - Backend" -> "quality assurance engineer backend"
        """
        if not title:
            return ""

        # Convert to lowercase
        normalized = title.lower()

        # Remove special characters but keep spaces and hyphens
        normalized = re.sub(r"[^\w\s-]", " ", normalized)

        # Split into words
        words = normalized.split()

        # Expand abbreviations
        expanded_words = []
        for word in words:
            # Check if word is an abbreviation
            clean_word = word.strip(".")
            if clean_word in self.TITLE_ABBREVIATIONS:
                expanded_words.append(self.TITLE_ABBREVIATIONS[clean_word])
            else:
                expanded_words.append(word)

        # Rejoin and normalize whitespace
        normalized = " ".join(expanded_words)

        # Remove hyphen-separated words (treat as space)
        normalized = normalized.replace("-", " ")

        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def normalize_location(self, location: str) -> str:
        """
        Normalize location for matching.

        Steps:
        1. Convert to lowercase
        2. Expand common abbreviations
        3. Handle remote variations
        4. Normalize state names
        5. Remove extra punctuation

        Args:
            location: Raw location string

        Returns:
            Normalized location string

        Examples:
            "San Francisco, CA" -> "san francisco california"
            "Remote - US" -> "remote"
            "NYC" -> "new york city"
        """
        if not location:
            return "unknown"

        # Convert to lowercase
        normalized = location.lower()

        # Check for common location patterns first
        if normalized in self.LOCATION_NORMALIZATIONS:
            return self.LOCATION_NORMALIZATIONS[normalized]

        # Remove punctuation except spaces and commas
        normalized = re.sub(r"[^\w\s,]", " ", normalized)

        # Split by comma to handle "City, State" format
        parts = [part.strip() for part in normalized.split(",")]

        # Process each part
        processed_parts = []
        for part in parts:
            words = part.split()
            expanded_words = []

            for word in words:
                # Check for state abbreviations (only if 2 characters)
                if len(word) == 2 and word in self.STATE_ABBREVIATIONS:
                    expanded_words.append(self.STATE_ABBREVIATIONS[word])
                # Check for location normalizations
                elif word in self.LOCATION_NORMALIZATIONS:
                    expanded_words.append(self.LOCATION_NORMALIZATIONS[word])
                else:
                    expanded_words.append(word)

            processed_parts.append(" ".join(expanded_words))

        # Join parts with space (not comma)
        normalized = " ".join(processed_parts)

        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized if normalized else "unknown"

    def create_signature(
        self, company_id: str, title: str, location: str
    ) -> str:
        """
        Create normalized signature for job matching.

        The signature combines company ID, normalized title, and normalized location
        to uniquely identify a job posting.

        Args:
            company_id: Company identifier
            title: Job title
            location: Job location

        Returns:
            Normalized signature string

        Example:
            company_id="acme-corp"
            title="Sr. Software Engineer"
            location="San Francisco, CA"
            -> "acme-corp|senior software engineer|san francisco california"
        """
        norm_title = self.normalize_title(title)
        norm_location = self.normalize_location(location)

        signature = f"{company_id}|{norm_title}|{norm_location}"

        self.logger.debug(
            f"Created signature: {signature} from "
            f"(company={company_id}, title={title}, location={location})"
        )

        return signature

    def get_normalization_details(
        self, title: str, location: str
    ) -> Dict[str, str]:
        """
        Get normalization details for debugging/explainability.

        Args:
            title: Original title
            location: Original location

        Returns:
            Dictionary with original and normalized values
        """
        return {
            "original_title": title,
            "normalized_title": self.normalize_title(title),
            "original_location": location,
            "normalized_location": self.normalize_location(location),
        }
