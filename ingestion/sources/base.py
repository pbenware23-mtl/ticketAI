"""
Base adapter for all ingestion sources.

Each source parses its native payload into a common dict/kwargs shape
and calls the central IngestionService.ingest().
"""

from abc import ABC, abstractmethod
from typing import Any

from ingestion.core import IngestionService
from ingestion.schema import NormalizedTicket


class BaseSourceAdapter(ABC):
    """Parse source-specific payload and call ingestion service."""

    def __init__(self, ingestion_service: IngestionService):
        self._ingestion = ingestion_service

    @abstractmethod
    def parse(self, payload: Any) -> dict[str, Any]:
        """
        Convert raw payload from this source into kwargs for IngestionService.ingest().
        Must at least include: source, raw_text; optionally subject, source_id, customer fields, etc.
        """
        ...

    def ingest(self, payload: Any) -> NormalizedTicket:
        """Parse payload and submit to ingestion service."""
        kwargs = self.parse(payload)
        return self._ingestion.ingest(**kwargs)
