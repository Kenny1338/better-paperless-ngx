"""Intelligent correspondent matching using LLM."""

from typing import List, Optional

from ..api.models import Correspondent
from ..core.logger import get_logger
from ..llm.base import LLMProvider

logger = get_logger(__name__)


class CorrespondentMatcher:
    """Match and manage correspondents intelligently."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """
        Initialize correspondent matcher.

        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider

    async def find_or_create_correspondent(
        self,
        document_content: str,
        extracted_name: str,
        existing_correspondents: List[Correspondent],
    ) -> str:
        """
        Find matching correspondent or determine if new one should be created.

        Args:
            document_content: Full document OCR text
            extracted_name: Correspondent name extracted from document
            existing_correspondents: List of existing correspondents in Paperless

        Returns:
            Best matching correspondent name (existing or new)
        """
        logger.info(
            "matching_correspondent",
            extracted_name=extracted_name,
            existing_count=len(existing_correspondents),
        )

        if not existing_correspondents:
            # No existing correspondents, use extracted name
            logger.info("no_existing_correspondents", using=extracted_name)
            return extracted_name

        # Build prompt for LLM to match
        prompt = self._build_matching_prompt(
            document_content, extracted_name, existing_correspondents
        )

        try:
            response = await self.llm.generate_completion(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent matching
                max_tokens=200,
            )

            matched_name = response.content.strip()

            # Check if LLM suggested an existing correspondent
            for corr in existing_correspondents:
                if corr.name.lower() in matched_name.lower() or matched_name.lower() in corr.name.lower():
                    logger.info(
                        "correspondent_matched",
                        extracted=extracted_name,
                        matched_to=corr.name,
                        reason="llm_match",
                    )
                    return corr.name

            # Check if LLM said to create new
            if "new" in matched_name.lower() or "create" in matched_name.lower():
                logger.info(
                    "correspondent_new",
                    name=extracted_name,
                    reason="llm_suggested_new",
                )
                return extracted_name

            # If LLM returned a name from the list, use it
            logger.info(
                "correspondent_determined",
                original=extracted_name,
                final=matched_name,
            )
            return matched_name

        except Exception as e:
            logger.error("correspondent_matching_failed", error=str(e), exc_info=True)
            # Fallback to simple matching
            return self._simple_match(extracted_name, existing_correspondents)

    def _build_matching_prompt(
        self,
        document_content: str,
        extracted_name: str,
        existing_correspondents: List[Correspondent],
    ) -> str:
        """Build prompt for LLM correspondent matching."""
        # Limit document content to avoid token limits
        content_preview = document_content[:1500]

        # Build list of existing correspondents
        corr_list = "\n".join(
            [f"- {corr.name}" for corr in existing_correspondents[:50]]  # Limit to 50
        )

        prompt = f"""Du bist ein intelligenter Dokumenten-Assistent. Analysiere das folgende Dokument und bestimme den richtigen Correspondent (Absender/Vendor).

Dokumentinhalt (OCR):
{content_preview}

Extrahierter Correspondent-Name aus Dokument:
"{extracted_name}"

Existierende Correspondents in Paperless:
{corr_list}

Aufgabe:
1. Prüfe ob einer der existierenden Correspondents zu diesem Dokument passt
2. Berücksichtige Variationen (z.B. "EnBW AG" vs "EnBW Energie Baden-Württemberg AG")
3. Berücksichtige Abkürzungen und Schreibweisen

Wenn ein existierender Correspondent passt:
- Gib EXAKT den Namen des passenden Correspondents zurück

Wenn KEIN existierender passt:
- Gib den extrahierten Namen zurück: "{extracted_name}"

Antwort (nur der Name, keine Erklärung):"""

        return prompt

    def _simple_match(
        self, extracted_name: str, existing_correspondents: List[Correspondent]
    ) -> str:
        """
        Simple fuzzy matching fallback.

        Args:
            extracted_name: Name extracted from document
            existing_correspondents: Existing correspondents

        Returns:
            Best match or extracted name
        """
        extracted_lower = extracted_name.lower()

        # Try exact match
        for corr in existing_correspondents:
            if corr.name.lower() == extracted_lower:
                logger.info("correspondent_exact_match", matched_to=corr.name)
                return corr.name

        # Try substring match
        for corr in existing_correspondents:
            if extracted_lower in corr.name.lower() or corr.name.lower() in extracted_lower:
                logger.info("correspondent_fuzzy_match", matched_to=corr.name)
                return corr.name

        # Check for common abbreviations
        # e.g., "ARD ZDF" should match "ARD ZDF Deutschlandradio Beitragsservice"
        name_words = set(extracted_lower.split())
        for corr in existing_correspondents:
            corr_words = set(corr.name.lower().split())
            # If more than 50% of words match
            overlap = name_words & corr_words
            if len(overlap) / len(name_words) > 0.5:
                logger.info(
                    "correspondent_word_match",
                    matched_to=corr.name,
                    overlap=list(overlap),
                )
                return corr.name

        # No match found, use extracted name
        logger.info("correspondent_no_match", using_new=extracted_name)
        return extracted_name