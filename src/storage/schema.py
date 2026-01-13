"""
JSON Schema definitions for data storage.

All schemas include version fields for migration support.
"""

from typing import Dict, Any
from jsonschema import validate, ValidationError

JOB_RECORD_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "version": "1.0.0",
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "description": "Internal unique identifier (UUID)",
        },
        "company_id": {
            "type": "string",
            "description": "References company in config",
        },
        "company_name": {
            "type": "string",
        },
        "title": {
            "type": "string",
        },
        "location": {
            "type": "string",
        },
        "url": {
            "type": "string",
            "format": "uri",
        },
        "source_identifier": {
            "type": ["string", "null"],
            "description": "ATS-specific job ID",
        },
        "signature": {
            "type": "string",
            "description": "Normalized signature for matching",
        },
        "status": {
            "type": "string",
            "enum": ["active", "missing", "closed", "reopened"],
        },
        "classification": {
            "type": "string",
            "enum": ["new", "repost", "existing"],
        },
        "classification_reasoning": {
            "type": "string",
            "description": "Explanation of classification decision",
        },
        "first_seen": {
            "type": "string",
            "format": "date-time",
        },
        "last_seen": {
            "type": "string",
            "format": "date-time",
        },
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "source_identifier": {"type": ["string", "null"]},
                    "url": {"type": "string"},
                },
                "required": ["timestamp", "url"],
            },
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
        },
        "updated_at": {
            "type": "string",
            "format": "date-time",
        },
    },
    "required": [
        "id",
        "company_id",
        "company_name",
        "title",
        "location",
        "url",
        "signature",
        "status",
        "classification",
        "first_seen",
        "last_seen",
    ],
}

JOBS_COLLECTION_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "version": {
            "type": "string",
            "const": "1.0.0",
        },
        "generated_at": {
            "type": "string",
            "format": "date-time",
        },
        "jobs": {
            "type": "array",
            "items": JOB_RECORD_SCHEMA_V1,
        },
    },
    "required": ["version", "generated_at", "jobs"],
}

APPLICATION_RECORD_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "version": "1.0.0",
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "References job record",
        },
        "applied_date": {
            "type": "string",
            "format": "date",
        },
        "stage": {
            "type": "string",
            "enum": ["applied", "screening", "interview", "rejected", "offer"],
        },
        "notes": {
            "type": "string",
        },
        "contact_person": {
            "type": ["string", "null"],
        },
        "referral_source": {
            "type": ["string", "null"],
        },
        "salary_info": {
            "type": ["string", "null"],
        },
        "follow_ups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "format": "date-time"},
                    "type": {
                        "type": "string",
                        "enum": ["application", "follow-up"],
                    },
                    "notes": {"type": "string"},
                },
                "required": ["timestamp", "type"],
            },
        },
        "next_follow_up": {
            "type": ["string", "null"],
            "format": "date",
        },
    },
    "required": ["job_id", "applied_date", "stage"],
}

APPLICATIONS_COLLECTION_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "version": {
            "type": "string",
            "const": "1.0.0",
        },
        "applications": {
            "type": "array",
            "items": APPLICATION_RECORD_SCHEMA_V1,
        },
    },
    "required": ["version", "applications"],
}

# Schema registry for migration support
SCHEMA_VERSIONS = {
    "jobs": {
        "1.0.0": JOBS_COLLECTION_SCHEMA_V1,
    },
    "applications": {
        "1.0.0": APPLICATIONS_COLLECTION_SCHEMA_V1,
    },
}

# Current schema versions
CURRENT_SCHEMA_VERSION = {
    "jobs": "1.0.0",
    "applications": "1.0.0",
}


def validate_job_record(job_data: Dict[str, Any]) -> None:
    """
    Validate a job record against the schema.

    Args:
        job_data: Job data dictionary to validate

    Raises:
        ValidationError: If validation fails
    """
    validate(instance=job_data, schema=JOB_RECORD_SCHEMA_V1)


def validate_jobs_collection(data: Dict[str, Any]) -> None:
    """
    Validate a jobs collection against the schema.

    Args:
        data: Jobs collection data to validate

    Raises:
        ValidationError: If validation fails
    """
    validate(instance=data, schema=JOBS_COLLECTION_SCHEMA_V1)
