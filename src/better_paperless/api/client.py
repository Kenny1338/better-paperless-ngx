"""Paperless-ngx API client implementation."""

import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core.logger import get_logger
from .exceptions import (
    PaperlessAPIError,
    PaperlessAuthenticationError,
    PaperlessConnectionError,
    PaperlessNotFoundError,
    PaperlessRateLimitError,
)
from .models import Correspondent, Document, DocumentListResponse, DocumentType, Tag

logger = get_logger(__name__)


class PaperlessClient:
    """Client for interacting with Paperless-ngx API."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize Paperless client.

        Args:
            base_url: Base URL of Paperless instance
            api_token: API authentication token
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries

        self._client: Optional[httpx.AsyncClient] = None
        self._headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        }

    async def __aenter__(self) -> "PaperlessClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers=self._headers,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self._headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        return self._client

    def _build_url(self, endpoint: str) -> str:
        """Build full API URL from endpoint."""
        return urljoin(f"{self.base_url}/api/", endpoint.lstrip("/"))

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response

        Returns:
            Parsed JSON response

        Raises:
            PaperlessAPIError: For various API errors
        """
        if response.status_code == 401:
            raise PaperlessAuthenticationError(
                "Authentication failed. Check your API token.",
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise PaperlessNotFoundError(
                "Resource not found.",
                status_code=response.status_code,
            )

        if response.status_code == 429:
            raise PaperlessRateLimitError(
                "Rate limit exceeded. Please try again later.",
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_data)
            except Exception:
                error_data = {"detail": response.text}
                error_msg = response.text
            
            logger.error(
                "api_error_response",
                status_code=response.status_code,
                error_data=error_data,
                url=str(response.url),
                method=response.request.method
            )

            raise PaperlessAPIError(
                f"API error: {error_msg}",
                status_code=response.status_code,
                response_data=error_data,
            )

        try:
            return response.json()
        except Exception:
            return {}

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body

        Returns:
            Response data

        Raises:
            PaperlessConnectionError: For connection errors
            PaperlessAPIError: For API errors
        """
        client = self._get_client()
        url = self._build_url(endpoint)

        try:
            logger.debug(
                "api_request",
                method=method,
                endpoint=endpoint,
                params=params,
            )

            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json,
            )

            return await self._handle_response(response)

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error("connection_error", endpoint=endpoint, error=str(e))
            raise PaperlessConnectionError(
                f"Failed to connect to Paperless: {str(e)}"
            ) from e

    # Document Operations

    async def get_document(self, document_id: int) -> Document:
        """
        Get document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document object
        """
        data = await self._request("GET", f"documents/{document_id}/")
        return Document(**data)

    async def get_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        ordering: str = "-created",
    ) -> DocumentListResponse:
        """
        Get list of documents with optional filters.

        Args:
            filters: Filter parameters
            limit: Maximum number of results
            offset: Offset for pagination
            ordering: Field to order by (prefix with - for descending)

        Returns:
            List of documents with pagination info
        """
        params = {
            "page_size": limit,
            "offset": offset,
            "ordering": ordering,
        }

        if filters:
            params.update(filters)

        data = await self._request("GET", "documents/", params=params)
        return DocumentListResponse(**data)

    async def update_document(
        self,
        document_id: int,
        title: Optional[str] = None,
        tags: Optional[List[int]] = None,
        correspondent: Optional[int] = None,
        document_type: Optional[int] = None,
        created_date: Optional[str] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
    ) -> Document:
        """
        Update document metadata.

        Args:
            document_id: Document ID
            title: New title
            tags: List of tag IDs
            correspondent: Correspondent ID
            document_type: Document type ID
            created_date: Document date (ISO format)
            custom_fields: Custom field values

        Returns:
            Updated document
        """
        # Build update payload
        payload: Dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if tags is not None:
            payload["tags"] = tags
        if correspondent is not None:
            payload["correspondent"] = correspondent
        if document_type is not None:
            payload["document_type"] = document_type
        if created_date is not None:
            payload["created_date"] = created_date
        if custom_fields is not None:
            payload["custom_fields"] = custom_fields

        data = await self._request("PATCH", f"documents/{document_id}/", json=payload)
        return Document(**data)

    async def download_document_content(self, document_id: int) -> str:
        """
        Download document OCR text content.

        Args:
            document_id: Document ID

        Returns:
            Document text content
        """
        client = self._get_client()
        url = self._build_url(f"documents/{document_id}/download/")

        try:
            response = await client.get(url, params={"original": "false"})
            response.raise_for_status()

            # Try to get text content
            # Paperless provides text through the content field
            doc = await self.get_document(document_id)
            return doc.content or ""

        except Exception as e:
            logger.error("download_error", document_id=document_id, error=str(e))
            raise PaperlessAPIError(f"Failed to download document: {str(e)}") from e

    # Tag Operations

    async def get_tags(self) -> List[Tag]:
        """
        Get all tags.

        Returns:
            List of tags
        """
        data = await self._request("GET", "tags/")
        results = data.get("results", [])
        return [Tag(**tag) for tag in results]

    async def get_tag(self, tag_id: int) -> Tag:
        """
        Get tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Tag object
        """
        data = await self._request("GET", f"tags/{tag_id}/")
        return Tag(**data)

    async def create_tag(
        self,
        name: str,
        color: str = "#3498db",
        match: str = "",
        matching_algorithm: int = 1,
    ) -> Tag:
        """
        Create new tag.

        Args:
            name: Tag name
            color: Hex color code
            match: Matching pattern
            matching_algorithm: Algorithm for matching (1=Any, 2=All, 3=Literal, 4=Regex)

        Returns:
            Created tag
        """
        payload = {
            "name": name,
            "color": color,
            "match": match,
            "matching_algorithm": matching_algorithm,
        }

        data = await self._request("POST", "tags/", json=payload)
        return Tag(**data)

    async def get_or_create_tag(self, name: str, color: str = "#3498db") -> Tag:
        """
        Get existing tag or create new one.

        Args:
            name: Tag name
            color: Hex color code for new tag

        Returns:
            Tag object
        """
        # Try to find existing tag
        tags = await self.get_tags()
        for tag in tags:
            if tag.name.lower() == name.lower():
                return tag

        # Create new tag
        return await self.create_tag(name, color)

    # Correspondent Operations

    async def get_correspondents(self) -> List[Correspondent]:
        """
        Get all correspondents.

        Returns:
            List of correspondents
        """
        data = await self._request("GET", "correspondents/")
        results = data.get("results", [])
        return [Correspondent(**corr) for corr in results]

    async def create_correspondent(
        self,
        name: str,
        match: str = "",
        matching_algorithm: int = 1,
    ) -> Correspondent:
        """
        Create new correspondent.

        Args:
            name: Correspondent name
            match: Matching pattern
            matching_algorithm: Algorithm for matching

        Returns:
            Created correspondent
        """
        payload = {
            "name": name,
            "match": match,
            "matching_algorithm": matching_algorithm,
        }

        data = await self._request("POST", "correspondents/", json=payload)
        return Correspondent(**data)

    async def get_or_create_correspondent(self, name: str) -> Correspondent:
        """
        Get existing correspondent or create new one.

        Args:
            name: Correspondent name

        Returns:
            Correspondent object
        """
        # Try to find existing correspondent
        correspondents = await self.get_correspondents()
        for corr in correspondents:
            if corr.name.lower() == name.lower():
                return corr

        # Create new correspondent
        return await self.create_correspondent(name)

    # Document Type Operations

    async def get_document_types(self) -> List[DocumentType]:
        """
        Get all document types.

        Returns:
            List of document types
        """
        data = await self._request("GET", "document_types/")
        results = data.get("results", [])
        return [DocumentType(**dt) for dt in results]

    async def create_document_type(
        self,
        name: str,
        match: str = "",
        matching_algorithm: int = 1,
    ) -> DocumentType:
        """
        Create new document type.

        Args:
            name: Document type name
            match: Matching pattern
            matching_algorithm: Algorithm for matching

        Returns:
            Created document type
        """
        payload = {
            "name": name,
            "match": match,
            "matching_algorithm": matching_algorithm,
        }

        data = await self._request("POST", "document_types/", json=payload)
        return DocumentType(**data)

    async def get_or_create_document_type(self, name: str) -> DocumentType:
        """
        Get existing document type or create new one.

        Args:
            name: Document type name

        Returns:
            DocumentType object
        """
        # Try to find existing document type
        doc_types = await self.get_document_types()
        for dt in doc_types:
            if dt.name.lower() == name.lower():
                return dt

        # Create new document type
        return await self.create_document_type(name)

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None