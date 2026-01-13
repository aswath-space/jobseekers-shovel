"""
Input validation utilities.
"""

import re
from urllib.parse import urlparse
from typing import Optional


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate a URL format.

    Args:
        url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    try:
        result = urlparse(url)
        if not result.scheme:
            return False, "URL must include a scheme (http:// or https://)"
        if not result.netloc:
            return False, "URL must include a domain"
        if result.scheme not in ["http", "https"]:
            return False, "URL scheme must be http or https"
        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {e}"


def validate_company_id(company_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate a company ID format.

    Company IDs must be lowercase alphanumeric with hyphens only.

    Args:
        company_id: Company ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not company_id or not isinstance(company_id, str):
        return False, "Company ID must be a non-empty string"

    if not re.match(r"^[a-z0-9-]+$", company_id):
        return (
            False,
            "Company ID must be lowercase alphanumeric with hyphens only",
        )

    if company_id.startswith("-") or company_id.endswith("-"):
        return False, "Company ID cannot start or end with a hyphen"

    if "--" in company_id:
        return False, "Company ID cannot contain consecutive hyphens"

    return True, None


def validate_adapter_type(adapter: str) -> tuple[bool, Optional[str]]:
    """
    Validate adapter type.

    Args:
        adapter: Adapter type string

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_adapters = ["greenhouse", "lever", "workday"]

    if adapter not in valid_adapters:
        return (
            False,
            f"Invalid adapter '{adapter}'. Valid: {', '.join(valid_adapters)}",
        )

    return True, None
