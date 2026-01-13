"""
Fuzzy matching system for job signatures.

Uses rapidfuzz for efficient fuzzy string matching to detect similar jobs
even with minor variations in title or location.
"""

from typing import List, Tuple, Optional
from rapidfuzz import fuzz, process

from src.utils.logging import get_logger


class JobMatcher:
    """
    Fuzzy matcher for job signatures.

    Detects similar jobs based on normalized signatures using configurable
    similarity thresholds.
    """

    def __init__(self, similarity_threshold: float = 0.90):
        """
        Initialize matcher.

        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0) for a match
                                 Default: 0.90 (90% similar)
        """
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                f"Similarity threshold must be between 0.0 and 1.0, got {similarity_threshold}"
            )

        self.similarity_threshold = similarity_threshold
        self.logger = get_logger(__name__)

    def calculate_similarity(self, signature1: str, signature2: str) -> float:
        """
        Calculate similarity score between two signatures.

        Uses component-wise comparison with combined scoring for better accuracy:
        - Compares company, title, and location separately
        - Uses max(token_set_ratio, token_sort_ratio) for title to handle word order
        - Uses exact ratio for company and location
        - Combines scores with weighted average

        Args:
            signature1: First signature (format: "company|title|location")
            signature2: Second signature (format: "company|title|location")

        Returns:
            Similarity score between 0.0 and 1.0

        Example:
            >>> matcher = JobMatcher()
            >>> matcher.calculate_similarity(
            ...     "acme|senior engineer|san francisco",
            ...     "acme|senior software engineer|san francisco"
            ... )
            0.95
        """
        # Split signatures into components
        parts1 = signature1.split('|')
        parts2 = signature2.split('|')

        # If signatures don't have 3 parts, fall back to full string comparison
        if len(parts1) != 3 or len(parts2) != 3:
            score = fuzz.token_set_ratio(signature1, signature2)
            return score / 100.0

        company1, title1, location1 = parts1
        company2, title2, location2 = parts2

        # Company match (exact comparison)
        company_score = fuzz.ratio(company1, company2)

        # Title match: Use token_sort_ratio which handles reordering but penalizes extra words
        # token_sort_ratio sorts tokens before comparison, so "research engineer machine learning"
        # matches "machine learning research engineer" well, but "software engineer" vs
        # "senior software engineer" gets penalized for the extra "senior" word
        title_score = fuzz.token_sort_ratio(title1, title2)

        # Location match (exact comparison, penalizes qualifiers like "hybrid")
        location_score = fuzz.ratio(location1, location2)

        # Weighted average: title is most important, then location, then company
        # Title: 60%, Location: 30%, Company: 10%
        combined_score = (
            0.10 * company_score +
            0.60 * title_score +
            0.30 * location_score
        )

        # Convert from 0-100 scale to 0.0-1.0
        return combined_score / 100.0

    def is_match(self, signature1: str, signature2: str) -> bool:
        """
        Check if two signatures match based on threshold.

        Args:
            signature1: First signature
            signature2: Second signature

        Returns:
            True if signatures match (similarity >= threshold)
        """
        similarity = self.calculate_similarity(signature1, signature2)
        is_match = similarity >= self.similarity_threshold

        if is_match:
            self.logger.debug(
                f"Match found (similarity={similarity:.2f}): "
                f"'{signature1}' <-> '{signature2}'"
            )

        return is_match

    def find_best_match(
        self,
        query_signature: str,
        candidate_signatures: List[str],
        return_score: bool = False
    ) -> Optional[str] | Tuple[Optional[str], float]:
        """
        Find best matching signature from a list of candidates.

        Args:
            query_signature: Signature to match
            candidate_signatures: List of candidate signatures
            return_score: If True, return (match, score) tuple

        Returns:
            Best matching signature if above threshold, else None
            If return_score=True, returns (signature, score) tuple

        Example:
            >>> matcher = JobMatcher()
            >>> candidates = [
            ...     "acme|engineer|boston",
            ...     "acme|senior engineer|san francisco",
            ...     "acme|manager|new york"
            ... ]
            >>> matcher.find_best_match(
            ...     "acme|sr engineer|sf",
            ...     candidates
            ... )
            "acme|senior engineer|san francisco"
        """
        if not candidate_signatures:
            return (None, 0.0) if return_score else None

        # Calculate similarity for each candidate using our calculate_similarity method
        best_match = None
        best_score = 0.0

        for candidate in candidate_signatures:
            score = self.calculate_similarity(query_signature, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        # Check if best score meets threshold
        if best_score >= self.similarity_threshold:
            self.logger.debug(
                f"Best match found (similarity={best_score:.2f}): "
                f"'{query_signature}' -> '{best_match}'"
            )

            if return_score:
                return (best_match, best_score)
            return best_match

        # No match above threshold
        if return_score:
            return (None, best_score)
        return None

    def find_all_matches(
        self,
        query_signature: str,
        candidate_signatures: List[str],
        limit: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Find all matching signatures above threshold.

        Args:
            query_signature: Signature to match
            candidate_signatures: List of candidate signatures
            limit: Maximum number of matches to return (None = all)

        Returns:
            List of (signature, score) tuples, sorted by score descending

        Example:
            >>> matcher = JobMatcher()
            >>> candidates = [
            ...     "acme|senior engineer|sf",
            ...     "acme|senior software engineer|san francisco",
            ...     "acme|engineer senior|sf"
            ... ]
            >>> matches = matcher.find_all_matches(
            ...     "acme|sr software engineer|san francisco",
            ...     candidates
            ... )
            >>> len(matches)
            3
        """
        if not candidate_signatures:
            return []

        # Calculate similarity for each candidate using our calculate_similarity method
        matches = []
        for candidate in candidate_signatures:
            score = self.calculate_similarity(query_signature, candidate)
            if score >= self.similarity_threshold:
                matches.append((candidate, score))

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        # Apply limit if specified
        if limit is not None and limit > 0:
            matches = matches[:limit]

        self.logger.debug(
            f"Found {len(matches)} matches for '{query_signature}' "
            f"(threshold={self.similarity_threshold})"
        )

        return matches

    def get_match_explanation(
        self,
        signature1: str,
        signature2: str
    ) -> dict:
        """
        Get detailed explanation of match result for debugging/explainability.

        Args:
            signature1: First signature
            signature2: Second signature

        Returns:
            Dictionary with match details

        Example:
            >>> matcher = JobMatcher()
            >>> matcher.get_match_explanation(
            ...     "acme|sr engineer|sf",
            ...     "acme|senior engineer|san francisco"
            ... )
            {
                "signature1": "acme|sr engineer|sf",
                "signature2": "acme|senior engineer|san francisco",
                "similarity": 0.95,
                "threshold": 0.90,
                "is_match": True,
                "reason": "Similarity (0.95) >= threshold (0.90)"
            }
        """
        similarity = self.calculate_similarity(signature1, signature2)
        is_match = similarity >= self.similarity_threshold

        return {
            "signature1": signature1,
            "signature2": signature2,
            "similarity": round(similarity, 3),
            "threshold": self.similarity_threshold,
            "is_match": is_match,
            "reason": (
                f"Similarity ({similarity:.2f}) "
                f"{'>=':6} threshold ({self.similarity_threshold})"
                if is_match
                else f"Similarity ({similarity:.2f}) "
                     f"{'<':6} threshold ({self.similarity_threshold})"
            )
        }
