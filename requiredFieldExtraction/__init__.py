"""
Required field extraction module (README §2).

Structured extraction from tickets: customer name, company, account ID,
product/module, environment, error message, timestamp, steps to reproduce,
attachments; plus issue type and urgency. Optional merge with ticket customer metadata.
"""

from requiredFieldExtraction.schema import ExtractedFields, ExtractionResult
from requiredFieldExtraction.service import ExtractionService
from requiredFieldExtraction.extractor import FieldExtractor

__all__ = [
    "ExtractedFields",
    "ExtractionResult",
    "ExtractionService",
    "FieldExtractor",
]
