"""Intelligent tagging engine for documents."""

import re
from typing import List, Optional, Set

from langdetect import detect

from ..core.logger import get_logger
from ..llm.base import LLMProvider
from ..llm.prompts import PromptTemplates

logger = get_logger(__name__)


class TagEngine:
    """Generate and manage document tags."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        use_rule_based: bool = True,
        use_llm: bool = True,
        confidence_threshold: float = 0.7,
    ) -> None:
        """
        Initialize tag engine.

        Args:
            llm_provider: LLM provider instance
            use_rule_based: Enable rule-based tagging
            use_llm: Enable LLM-based tagging
            confidence_threshold: Minimum confidence for LLM tags
        """
        self.llm = llm_provider
        self.use_rule_based = use_rule_based
        self.use_llm = use_llm
        self.confidence_threshold = confidence_threshold
        self.prompts = PromptTemplates()

        # Rule-based patterns
        self.tag_rules = self._load_default_rules()

    def _load_default_rules(self) -> List[dict]:
        """Load default tagging rules."""
        return [
            {
                "pattern": r"\b(invoice|rechnung|factura)\b",
                "tags": ["invoice", "financial"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(receipt|quittung|bon)\b",
                "tags": ["receipt", "financial"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(bank statement|kontoauszug)\b",
                "tags": ["bank-statement", "financial"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(contract|vertrag)\b",
                "tags": ["contract"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(insurance|versicherung)\b",
                "tags": ["insurance"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(tax|steuer|finanzamt)\b",
                "tags": ["tax", "important"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(electricity|strom|energie)\b",
                "tags": ["utility", "electricity"],
                "case_insensitive": True,
            },
            {
                "pattern": r"\b(water|wasser)\b",
                "tags": ["utility", "water"],
                "case_insensitive": True,
            },
        ]

    def _apply_rule_based_tags(self, content: str) -> Set[str]:
        """
        Apply rule-based tagging.

        Args:
            content: Document content

        Returns:
            Set of matched tags
        """
        tags: Set[str] = set()

        for rule in self.tag_rules:
            pattern = rule["pattern"]
            flags = re.IGNORECASE if rule.get("case_insensitive") else 0

            if re.search(pattern, content, flags):
                tags.update(rule["tags"])
                logger.debug("rule_matched", pattern=pattern, tags=rule["tags"])

        return tags

    async def _apply_llm_tags(
        self,
        content: str,
        existing_tags: Optional[List[str]] = None,
        max_tags: int = 10,
    ) -> Set[str]:
        """
        Apply LLM-based tagging.

        Args:
            content: Document content
            existing_tags: Existing tags in system
            max_tags: Maximum number of tags

        Returns:
            Set of LLM-suggested tags
        """
        try:
            # Detect language
            language = detect(content[:500]) if len(content) > 100 else "en"

            # Generate prompt
            prompt = self.prompts.tag_generation(
                content=content,
                existing_tags=existing_tags,
                max_tags=max_tags,
                language=language,
            )

            # Get LLM response
            response = await self.llm.generate_completion(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
            )

            # Parse tags from response
            tags_text = response.content.strip()
            tags = self._parse_tag_list(tags_text)

            logger.info(
                "llm_tags_generated",
                tags=list(tags),
                tokens_used=response.tokens_used,
                cost=response.cost,
            )

            return tags

        except Exception as e:
            logger.error("llm_tagging_failed", error=str(e), exc_info=True)
            return set()

    def _parse_tag_list(self, tags_text: str) -> Set[str]:
        """
        Parse comma-separated tag list.

        Args:
            tags_text: Raw tag text from LLM

        Returns:
            Set of normalized tags
        """
        # Split by comma or newline
        tags = re.split(r"[,\n]", tags_text)

        # Normalize each tag
        normalized = set()
        for tag in tags:
            tag = tag.strip().lower()
            # Remove quotes and extra whitespace
            tag = tag.strip('"\'')
            # Replace spaces with hyphens
            tag = re.sub(r"\s+", "-", tag)
            # Remove invalid characters
            tag = re.sub(r"[^a-z0-9_-]", "", tag)

            if tag and len(tag) > 1:
                normalized.add(tag)

        return normalized

    async def generate_tags(
        self,
        content: str,
        existing_tags: Optional[List[str]] = None,
        max_tags: int = 10,
    ) -> List[str]:
        """
        Generate tags for document using hybrid approach.

        Args:
            content: Document content
            existing_tags: Existing tags in Paperless system
            max_tags: Maximum number of tags to return

        Returns:
            List of suggested tags
        """
        logger.info("generating_tags", content_length=len(content))

        all_tags: Set[str] = set()

        # Apply rule-based tagging
        if self.use_rule_based:
            rule_tags = self._apply_rule_based_tags(content)
            all_tags.update(rule_tags)
            logger.debug("rule_based_tags", tags=list(rule_tags))

        # Apply LLM-based tagging
        if self.use_llm:
            llm_tags = await self._apply_llm_tags(content, existing_tags, max_tags)
            all_tags.update(llm_tags)
            logger.debug("llm_based_tags", tags=list(llm_tags))

        # Convert to sorted list and limit
        final_tags = sorted(all_tags)[:max_tags]

        logger.info("tags_generated", tags=final_tags, count=len(final_tags))

        return final_tags

    def load_custom_rules(self, rules: List[dict]) -> None:
        """
        Load custom tagging rules.

        Args:
            rules: List of rule dictionaries
        """
        self.tag_rules.extend(rules)
        logger.info("custom_rules_loaded", count=len(rules))