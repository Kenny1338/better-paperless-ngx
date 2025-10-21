"""Exceptions for Paperless API interactions."""


class PaperlessAPIError(Exception):
    """Base exception for Paperless API errors."""

    def __init__(self, message: str, status_code: int = 0, response_data: dict = None) -> None:
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Response data from API
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class PaperlessConnectionError(PaperlessAPIError):
    """Exception for connection errors."""

    pass


class PaperlessAuthenticationError(PaperlessAPIError):
    """Exception for authentication errors."""

    pass


class PaperlessNotFoundError(PaperlessAPIError):
    """Exception for resource not found errors."""

    pass


class PaperlessValidationError(PaperlessAPIError):
    """Exception for validation errors."""

    pass


class PaperlessRateLimitError(PaperlessAPIError):
    """Exception for rate limit errors."""

    pass