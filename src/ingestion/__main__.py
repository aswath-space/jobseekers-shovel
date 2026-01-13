"""
Entry point for running ingestion as a module.

Usage:
    python -m src.ingestion
"""

from src.ingestion.orchestrator import main

if __name__ == "__main__":
    main()
