"""Pipeline package for the Agentic AI Architect system."""
from .ingestion import IngestionPipeline
from .processing import ContentProcessor

__all__ = ["IngestionPipeline", "ContentProcessor"]
