"""Input validation utilities for Better Paperless."""

import re
from datetime import datetime
from typing import Any, List, Optional
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_api_token(token: str) -> bool:
    """
    Validate API token format.

    Args:
        token: API token to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(token and len(token) > 10)


def validate_document_id(document_id: Any) -> bool:
    """
    Validate document ID.

    Args:
        document_id: Document ID to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        return int(document_id) > 0
    except (ValueError, TypeError):
        return False


def validate_tag_name(name: str) -> bool:
    """
    Validate tag name format.

    Args:
        name: Tag name to validate

    Returns:
        True if valid, False otherwise
    """
    # Tag names should be lowercase, alphanumeric with hyphens/underscores
    pattern = r"^[a-z0-9_-]+$"
    return bool(re.match(pattern, name) and len(name) > 0 and len(name) <= 100)


def validate_color_hex(color: str) -> bool:
    """
    Validate hex color code.

    Args:
        color: Hex color code to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^#[0-9A-Fa-f]{6}$"
    return bool(re.match(pattern, color))


def validate_date_string(date_str: str) -> Optional[datetime]:
    """
    Validate and parse date string.

    Args:
        date_str: Date string to validate

    Returns:
        Parsed datetime object or None if invalid
    """
    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, "_", filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(". ")

    # Limit length
    max_length = 255
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
        name = name[: max_length - len(ext) - 1]
        sanitized = f"{name}.{ext}" if ext else name

    return sanitized


def validate_confidence_score(score: float) -> bool:
    """
    Validate confidence score is between 0 and 1.

    Args:
        score: Confidence score to validate

    Returns:
        True if valid, False otherwise
    """
    return 0.0 <= score <= 1.0


def validate_processing_options(options: dict) -> List[str]:
    """
    Validate processing options dictionary.

    Args:
        options: Processing options to validate

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check required fields
    if "llm_provider" in options:
        valid_providers = ["openai", "anthropic", "ollama"]
        if options["llm_provider"] not in valid_providers:
            errors.append(
                f"Invalid LLM provider: {options['llm_provider']}. "
                f"Must be one of {valid_providers}"
            )

    # Validate numeric ranges
    if "llm_temperature" in options:
        temp = options["llm_temperature"]
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
            errors.append("llm_temperature must be between 0 and 2")

    if "llm_max_tokens" in options:
        tokens = options["llm_max_tokens"]
        if not isinstance(tokens, int) or tokens < 1 or tokens > 100000:
            errors.append("llm_max_tokens must be between 1 and 100000")

    if "tag_confidence_threshold" in options:
        threshold = options["tag_confidence_threshold"]
        if not validate_confidence_score(threshold):
            errors.append("tag_confidence_threshold must be between 0 and 1")

    if "max_tags_per_document" in options:
        max_tags = options["max_tags_per_document"]
        if not isinstance(max_tags, int) or max_tags < 1 or max_tags > 50:
            errors.append("max_tags_per_document must be between 1 and 50")

    # Validate summary style
    if "summary_style" in options:
        valid_styles = ["concise", "detailed", "bullet_points"]
        if options["summary_style"] not in valid_styles:
            errors.append(
                f"Invalid summary style: {options['summary_style']}. "
                f"Must be one of {valid_styles}"
            )

    return errors


def validate_llm_response(response: dict) -> bool:
    """
    Validate LLM response structure.

    Args:
        response: LLM response to validate

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["content"]
    return all(field in response for field in required_fields)