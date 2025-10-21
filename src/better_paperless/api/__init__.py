"""Paperless-ngx API client and models."""

from .client import PaperlessClient
from .exceptions import (
    PaperlessAPIError,
    PaperlessAuthenticationError,
    PaperlessConnectionError,
    PaperlessNotFoundError,
)
from .models import Correspondent, CustomField, Document, DocumentType, Tag

__all__ = [
    "PaperlessClient",
    "Document",
    "Tag",
    "Correspondent",
    "DocumentType",
    "CustomField",
    "PaperlessAPIError",
    "PaperlessAuthenticationError",
    "PaperlessConnectionError",
    "PaperlessNotFoundError",
]