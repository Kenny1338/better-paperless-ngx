"""Main document processor orchestrating all processing steps."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..api.client import PaperlessClient
from ..core.config import ProcessingOptions
from ..core.logger import get_logger, log_processing_complete, log_processing_start
from ..llm.base import LLMProvider
from .correspondent_matcher import CorrespondentMatcher
from .metadata_extractor import MetadataExtractor
from .tag_engine import TagEngine
from .title_generator import TitleGenerator

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""

    document_id: int
    success: bool
    title: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    correspondent: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    llm_tokens_used: int = 0
    llm_cost: float = 0.0


class DocumentProcessor:
    """Main document processor orchestrating all processing steps."""

    def __init__(
        self,
        paperless_client: PaperlessClient,
        llm_provider: LLMProvider,
        options: ProcessingOptions,
    ) -> None:
        """
        Initialize document processor.

        Args:
            paperless_client: Paperless API client
            llm_provider: LLM provider instance
            options: Processing options
        """
        self.paperless = paperless_client
        self.llm = llm_provider
        self.options = options

        # Initialize sub-processors
        self.title_generator = TitleGenerator(llm_provider)
        self.tag_engine = TagEngine(
            llm_provider,
            use_rule_based=options.use_rule_based_tagging,
            use_llm=options.use_llm_tagging,
            confidence_threshold=options.tag_confidence_threshold,
        )
        self.metadata_extractor = MetadataExtractor(llm_provider)
        self.correspondent_matcher = CorrespondentMatcher(llm_provider)

    async def process_document(self, document_id: int) -> ProcessingResult:
        """
        Process a single document.

        Args:
            document_id: Paperless document ID

        Returns:
            ProcessingResult with all extracted information
        """
        start_time = time.time()
        result = ProcessingResult(document_id=document_id, success=False)

        log_processing_start(logger, document_id, "process_document")

        try:
            # Fetch document from Paperless
            document = await self.paperless.get_document(document_id)
            logger.debug("document_fetched", document_id=document_id, title=document.title)

            # Check if document was already processed
            if self.options.skip_if_processed_tag:
                all_tags = await self.paperless.get_tags()
                processed_tag_id = None
                for tag in all_tags:
                    if tag.name == self.options.processed_tag:
                        processed_tag_id = tag.id
                        break
                
                if processed_tag_id and processed_tag_id in document.tags:
                    logger.info(
                        "document_already_processed",
                        document_id=document_id,
                        reason=f"Has '{self.options.processed_tag}' tag"
                    )
                    result.success = True
                    result.processing_time = time.time() - start_time
                    return result

            # Get document content
            content = await self.paperless.download_document_content(document_id)
            if not content or len(content.strip()) < 10:
                raise ValueError("Document content is empty or too short")

            logger.debug("content_downloaded", content_length=len(content))

            # Track total tokens and cost
            total_tokens = 0
            total_cost = 0.0

            # Get existing tags for context
            existing_tag_names = await self._get_existing_tag_names()

            # Step 1: Generate title
            if self.options.enable_title_generation:
                if not self.options.skip_if_title_exists or not document.title or document.title == document.original_file_name:
                    title = await self.title_generator.generate_title(
                        content=content,
                        tags=[],
                        document_type=None,
                    )
                    result.title = title
                    logger.info("title_generated", title=title)
                else:
                    logger.debug("skipping_title_generation", reason="title_exists")

            # Step 2: Extract metadata
            if self.options.enable_metadata_extraction:
                metadata = await self.metadata_extractor.extract_metadata(content)
                result.metadata = metadata
                logger.info("metadata_extracted", metadata=metadata)

            # Step 3: Generate tags
            if self.options.enable_tagging:
                if not self.options.skip_if_tags_exist or not document.tags:
                    tags = await self.tag_engine.generate_tags(
                        content=content,
                        existing_tags=existing_tag_names,
                        max_tags=self.options.max_tags_per_document,
                    )
                    result.tags = tags
                    logger.info("tags_generated", tags=tags)
                else:
                    logger.debug("skipping_tag_generation", reason="tags_exist")

            # Step 4: Update document in Paperless
            await self._update_document(document_id, result, content)

            # Mark as successful
            result.success = True
            result.processing_time = time.time() - start_time

            log_processing_complete(
                logger,
                document_id,
                "process_document",
                result.processing_time,
                success=True,
                title=result.title,
                tags_count=len(result.tags),
            )

            return result

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            result.errors.append(error_msg)
            result.processing_time = time.time() - start_time

            logger.error(
                "processing_failed",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )

            log_processing_complete(
                logger,
                document_id,
                "process_document",
                result.processing_time,
                success=False,
                error=str(e),
            )

            return result

    async def _update_document(
        self,
        document_id: int,
        result: ProcessingResult,
        content: str = "",
    ) -> None:
        """
        Update document in Paperless with processed data.

        Args:
            document_id: Document ID
            result: Processing result
            content: Document OCR content for intelligent matching
        """
        update_data: Dict[str, Any] = {}

        # Add title
        if result.title:
            update_data["title"] = result.title

        # Add tags (including processed tag)
        if result.tags:
            tag_ids = await self._get_or_create_tag_ids(result.tags)
            
            # Add processed tag
            processed_tag = await self.paperless.get_or_create_tag(
                self.options.processed_tag,
                color="#2ecc71"  # Green color for processed
            )
            tag_ids.append(processed_tag.id)
            
            update_data["tags"] = tag_ids

        # Add correspondent with intelligent matching
        if result.metadata.get("correspondent"):
            # Get all existing correspondents
            existing_correspondents = await self.paperless.get_correspondents()
            
            # Use LLM to match or create correspondent
            matched_name = await self.correspondent_matcher.find_or_create_correspondent(
                document_content=content,
                extracted_name=result.metadata["correspondent"],
                existing_correspondents=existing_correspondents,
            )
            
            # Get or create the matched correspondent
            correspondent = await self.paperless.get_or_create_correspondent(matched_name)
            update_data["correspondent"] = correspondent.id
            
            logger.info(
                "correspondent_assigned",
                document_id=document_id,
                extracted=result.metadata["correspondent"],
                final=matched_name,
                correspondent_id=correspondent.id,
            )

        # Add document date
        if result.metadata.get("document_date"):
            update_data["created_date"] = result.metadata["document_date"]

        # Update document
        if update_data:
            await self.paperless.update_document(document_id, **update_data)
            logger.info("document_updated", document_id=document_id, updates=update_data)

    async def _get_or_create_tag_ids(self, tag_names: List[str]) -> List[int]:
        """
        Get or create tags and return their IDs.

        Args:
            tag_names: List of tag names

        Returns:
            List of tag IDs
        """
        tag_ids = []

        for tag_name in tag_names:
            try:
                tag = await self.paperless.get_or_create_tag(tag_name)
                tag_ids.append(tag.id)
            except Exception as e:
                logger.warning("tag_creation_failed", tag_name=tag_name, error=str(e))

        return tag_ids

    async def _get_existing_tag_names(self) -> List[str]:
        """
        Get list of existing tag names from Paperless.

        Returns:
            List of tag names
        """
        try:
            tags = await self.paperless.get_tags()
            return [tag.name for tag in tags]
        except Exception as e:
            logger.warning("failed_to_fetch_tags", error=str(e))
            return []

    async def process_batch(
        self,
        document_ids: List[int],
        max_concurrency: int = 5,
    ) -> List[ProcessingResult]:
        """
        Process multiple documents in parallel.

        Args:
            document_ids: List of document IDs to process
            max_concurrency: Maximum parallel processing tasks

        Returns:
            List of ProcessingResults
        """
        import asyncio

        logger.info("batch_processing_started", count=len(document_ids))

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_with_semaphore(doc_id: int) -> ProcessingResult:
            async with semaphore:
                return await self.process_document(doc_id)

        # Process all documents
        results = await asyncio.gather(
            *[process_with_semaphore(doc_id) for doc_id in document_ids],
            return_exceptions=True,
        )

        # Handle exceptions
        processed_results = []
        for doc_id, result in zip(document_ids, results):
            if isinstance(result, Exception):
                processed_results.append(
                    ProcessingResult(
                        document_id=doc_id,
                        success=False,
                        errors=[str(result)],
                    )
                )
            else:
                processed_results.append(result)

        # Log summary
        successful = sum(1 for r in processed_results if r.success)
        failed = len(processed_results) - successful

        logger.info(
            "batch_processing_completed",
            total=len(document_ids),
            successful=successful,
            failed=failed,
        )

        return processed_results