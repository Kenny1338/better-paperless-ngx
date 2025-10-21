"""Pydantic models for Paperless-ngx API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Tag(BaseModel):
    """Paperless tag model."""

    id: Optional[int] = None
    name: str
    slug: str = ""
    color: str = "#3498db"
    is_inbox_tag: bool = False
    text_color: str = "#ffffff"
    match: str = ""
    matching_algorithm: int = 1
    is_insensitive: bool = True
    document_count: int = 0

    class Config:
        """Pydantic config."""

        from_attributes = True


class Correspondent(BaseModel):
    """Paperless correspondent model."""

    id: Optional[int] = None
    name: str
    slug: str = ""
    match: str = ""
    matching_algorithm: int = 1
    is_insensitive: bool = True
    document_count: int = 0
    last_correspondence: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class DocumentType(BaseModel):
    """Paperless document type model."""

    id: Optional[int] = None
    name: str
    slug: str = ""
    match: str = ""
    matching_algorithm: int = 1
    is_insensitive: bool = True
    document_count: int = 0

    class Config:
        """Pydantic config."""

        from_attributes = True


class CustomField(BaseModel):
    """Paperless custom field model."""

    id: Optional[int] = None
    name: str
    data_type: str  # string, integer, float, date, boolean, url, monetary
    value: Any = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class Document(BaseModel):
    """Paperless document model."""

    id: int
    title: str
    content: Optional[str] = None
    created: datetime
    modified: datetime
    added: datetime
    correspondent: Optional[int] = None
    document_type: Optional[int] = None
    tags: List[int] = Field(default_factory=list)
    archive_serial_number: Optional[int] = None
    original_file_name: str = ""
    archived_file_name: Optional[str] = None
    created_date: Optional[datetime] = None
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[Dict[str, Any]] = Field(default_factory=list)

    # Additional metadata
    checksum: str = ""
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    owner: Optional[int] = None
    user_can_change: bool = True

    class Config:
        """Pydantic config."""

        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document list endpoint."""

    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    all: List[int] = Field(default_factory=list)
    results: List[Document] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        from_attributes = True


class BulkUpdateRequest(BaseModel):
    """Request model for bulk document updates."""

    documents: List[int]
    method: str = "set_correspondent"  # set_correspondent, add_tag, remove_tag, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        from_attributes = True


class SearchResult(BaseModel):
    """Search result model."""

    document_id: int
    title: str
    content_preview: str
    score: float
    highlights: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        from_attributes = True