"""Title generation for documents."""

import re
from typing import List, Optional

from langdetect import detect

from ..core.logger import get_logger
from ..llm.base import LLMProvider
from ..llm.prompts import PromptTemplates

logger = get_logger(__name__)


class TitleGenerator:
    """Generate descriptive titles for documents."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        """
        Initialize title generator.

        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
        self.prompts = PromptTemplates()

    def _detect_language(self, content: str) -> str:
        """
        Detect document language.

        Args:
            content: Document content

        Returns:
            Language code (en, de, etc.)
        """
        try:
            # Use first 500 chars for language detection
            sample = content[:500]
            lang = detect(sample)
            logger.debug("language_detected", language=lang)
            return lang
        except Exception as e:
            logger.warning("language_detection_failed", error=str(e))
            return "en"

    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize generated title.

        Args:
            title: Raw title

        Returns:
            Cleaned title
        """
        # Remove quotes
        title = title.strip('"\'')

        # Remove common prefixes
        prefixes = ["Title:", "Titel:", "Document:", "Dokument:"]
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()

        # Limit length
        if len(title) > 100:
            title = title[:97] + "..."

        # Clean up whitespace
        title = " ".join(title.split())

        return title

    async def generate_title(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        document_type: Optional[str] = None,
    ) -> str:
        """
        Generate title for document.

        Args:
            content: Document content
            tags: Existing tags
            document_type: Document type

        Returns:
            Generated title
        """
        logger.info("generating_title", content_length=len(content))

        try:
            # Detect language
            language = self._detect_language(content)

            # Generate prompt
            prompt = self.prompts.title_generation(
                content=content,
                tags=tags,
                document_type=document_type,
                language=language,
            )

            # Generate title using LLM
            response = await self.llm.generate_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=100,
            )

            # Clean and return title
            title = self._clean_title(response.content)

            logger.info(
                "title_generated",
                title=title,
                tokens_used=response.tokens_used,
                cost=response.cost,
            )

            return title

        except Exception as e:
            logger.error("title_generation_failed", error=str(e), exc_info=True)
            # Fallback: extract from first line or use generic title
            return self._generate_fallback_title(content)

    def _generate_fallback_title(self, content: str) -> str:
        """
        Generate fallback title from content.

        Args:
            content: Document content

        Returns:
            Fallback title
        """
        # Try to extract from first line
        first_line = content.split("\n")[0].strip()

        if len(first_line) > 10 and len(first_line) < 100:
            return first_line

        # Use generic title with date
        from datetime import datetime

        return f"Document {datetime.now().strftime('%Y-%m-%d')}"