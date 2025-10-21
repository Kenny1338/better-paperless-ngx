"""Metadata extraction from documents."""

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from dateutil import parser as date_parser
from langdetect import detect

from ..core.logger import get_logger
from ..llm.base import LLMProvider
from ..llm.prompts import PromptTemplates

logger = get_logger(__name__)


class MetadataExtractor:
    """Extract metadata from document content."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """
        Initialize metadata extractor.

        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
        self.prompts = PromptTemplates()

    async def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from document content.

        Args:
            content: Document content

        Returns:
            Dictionary of extracted metadata
        """
        logger.info("extracting_metadata", content_length=len(content))

        metadata: Dict[str, Any] = {}

        try:
            # Detect language
            language = detect(content[:500]) if len(content) > 100 else "en"

            # Use LLM for extraction
            llm_metadata = await self._extract_with_llm(content, language)
            metadata.update(llm_metadata)

            # Apply rule-based extraction for validation
            rule_metadata = self._extract_with_rules(content)

            # Merge results, preferring rule-based for dates
            if rule_metadata.get("document_date") and not metadata.get("document_date"):
                metadata["document_date"] = rule_metadata["document_date"]

            logger.info("metadata_extracted", metadata=metadata)

            return metadata

        except Exception as e:
            logger.error("metadata_extraction_failed", error=str(e), exc_info=True)
            # Return rule-based fallback
            return self._extract_with_rules(content)

    async def _extract_with_llm(self, content: str, language: str) -> Dict[str, Any]:
        """
        Extract metadata using LLM.

        Args:
            content: Document content
            language: Document language

        Returns:
            Extracted metadata
        """
        # Generate prompt
        prompt = self.prompts.metadata_extraction(content, language)

        # Get structured output
        schema = self.prompts.create_structured_schema([
            "document_date",
            "correspondent",
            "amount",
            "currency",
            "invoice_number",
            "due_date",
        ])

        try:
            response = await self.llm.generate_structured_output(
                prompt=prompt,
                schema=schema,
                temperature=0.1,
            )

            metadata = response.data

            # Validate and normalize dates
            if metadata.get("document_date"):
                metadata["document_date"] = self._normalize_date(metadata["document_date"])

            if metadata.get("due_date"):
                metadata["due_date"] = self._normalize_date(metadata["due_date"])

            # Clean up null values
            metadata = {k: v for k, v in metadata.items() if v is not None}

            logger.debug(
                "llm_metadata_extracted",
                metadata=metadata,
                tokens=response.tokens_used,
                cost=response.cost,
            )

            return metadata

        except Exception as e:
            logger.error("llm_extraction_failed", error=str(e))
            return {}

    def _extract_with_rules(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata using regex patterns.

        Args:
            content: Document content

        Returns:
            Extracted metadata
        """
        metadata: Dict[str, Any] = {}

        # Extract dates
        date = self._extract_date(content)
        if date:
            metadata["document_date"] = date

        # Extract amounts
        amount_data = self._extract_amount(content)
        if amount_data:
            metadata.update(amount_data)

        # Extract invoice number
        invoice_num = self._extract_invoice_number(content)
        if invoice_num:
            metadata["invoice_number"] = invoice_num

        return metadata

    def _extract_date(self, content: str) -> Optional[str]:
        """
        Extract date from content.

        Args:
            content: Document content

        Returns:
            ISO format date string or None
        """
        # Common date patterns
        patterns = [
            r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b",  # DD.MM.YYYY or DD/MM/YYYY
            r"\b(\d{4}[./-]\d{1,2}[./-]\d{1,2})\b",  # YYYY-MM-DD
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",  # DD Mon YYYY
        ]

        dates_found = []

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    parsed = date_parser.parse(match.group(1), fuzzy=False)
                    # Only accept reasonable dates (not in future, not too old)
                    if 1990 <= parsed.year <= datetime.now().year + 1:
                        dates_found.append(parsed)
                except Exception:
                    continue

        if dates_found:
            # Return the most recent date
            most_recent = max(dates_found)
            return most_recent.strftime("%Y-%m-%d")

        return None

    def _extract_amount(self, content: str) -> Dict[str, Any]:
        """
        Extract monetary amounts from content.

        Args:
            content: Document content

        Returns:
            Dictionary with amount and currency
        """
        # Patterns for amounts with currency symbols
        patterns = [
            (r"€\s*(\d+[.,]\d{2})", "EUR"),
            (r"(\d+[.,]\d{2})\s*€", "EUR"),
            (r"\$\s*(\d+[.,]\d{2})", "USD"),
            (r"(\d+[.,]\d{2})\s*USD", "USD"),
            (r"£\s*(\d+[.,]\d{2})", "GBP"),
        ]

        for pattern, currency in patterns:
            matches = re.finditer(pattern, content)
            amounts = []

            for match in matches:
                try:
                    amount_str = match.group(1).replace(",", ".")
                    amount = float(amount_str)
                    amounts.append(amount)
                except ValueError:
                    continue

            if amounts:
                # Return the largest amount found
                max_amount = max(amounts)
                return {"amount": max_amount, "currency": currency}

        return {}

    def _extract_invoice_number(self, content: str) -> Optional[str]:
        """
        Extract invoice number from content.

        Args:
            content: Document content

        Returns:
            Invoice number or None
        """
        patterns = [
            r"(?:Invoice|Rechnung|Factura)\s*(?:No\.?|Nr\.?|#)?\s*:?\s*([A-Z0-9-]+)",
            r"(?:Invoice|Rechnung)\s+([A-Z]{2,}\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date to ISO format.

        Args:
            date_str: Date string in various formats

        Returns:
            ISO format date (YYYY-MM-DD)
        """
        try:
            parsed = date_parser.parse(date_str)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return date_str