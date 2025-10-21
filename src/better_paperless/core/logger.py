"""Structured logging setup for Better Paperless."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import FilteringBoundLogger


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[Path] = None,
    log_to_console: bool = True,
) -> None:
    """
    Set up structured logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format for logs ('json' or 'text')
        log_file: Optional path to log file
        log_to_console: Whether to log to console
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
        stream=sys.stdout if log_to_console else None,
    )

    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add appropriate renderer based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set up file logging if path provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding context to logs."""

    def __init__(self, **context: Any) -> None:
        """
        Initialize log context.

        Args:
            **context: Key-value pairs to add to log context
        """
        self.context = context
        self.token: Optional[Any] = None

    def __enter__(self) -> "LogContext":
        """Enter context and bind context variables."""
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and clear context variables."""
        structlog.contextvars.clear_contextvars()


def log_function_call(logger: FilteringBoundLogger, func_name: str, **kwargs: Any) -> None:
    """
    Log a function call with its parameters.

    Args:
        logger: Logger instance
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger.debug(
        "function_call",
        function=func_name,
        parameters={k: v for k, v in kwargs.items() if not k.startswith("_")},
    )


def log_processing_start(
    logger: FilteringBoundLogger, document_id: int, operation: str
) -> None:
    """
    Log the start of document processing.

    Args:
        logger: Logger instance
        document_id: ID of document being processed
        operation: Operation being performed
    """
    logger.info(
        "processing_started",
        document_id=document_id,
        operation=operation,
    )


def log_processing_complete(
    logger: FilteringBoundLogger,
    document_id: int,
    operation: str,
    duration: float,
    success: bool = True,
    **metadata: Any,
) -> None:
    """
    Log the completion of document processing.

    Args:
        logger: Logger instance
        document_id: ID of document processed
        operation: Operation performed
        duration: Processing duration in seconds
        success: Whether processing was successful
        **metadata: Additional metadata to log
    """
    logger.info(
        "processing_completed",
        document_id=document_id,
        operation=operation,
        duration_seconds=round(duration, 2),
        success=success,
        **metadata,
    )


def log_llm_request(
    logger: FilteringBoundLogger,
    provider: str,
    model: str,
    tokens: int,
    cost: float,
) -> None:
    """
    Log an LLM API request.

    Args:
        logger: Logger instance
        provider: LLM provider name
        model: Model name
        tokens: Number of tokens used
        cost: Estimated cost in USD
    """
    logger.debug(
        "llm_request",
        provider=provider,
        model=model,
        tokens=tokens,
        cost_usd=round(cost, 4),
    )


def log_error(
    logger: FilteringBoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    operation: Optional[str] = None,
) -> None:
    """
    Log an error with context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
        operation: Operation that failed
    """
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        operation=operation,
        context=context or {},
        exc_info=True,
    )