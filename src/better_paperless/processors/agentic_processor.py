"""Agentic document processor - LLM decides everything."""

import json
import time
from typing import Any, Dict, List, Optional

from ..api.client import PaperlessClient
from ..api.models import Correspondent, Tag
from ..core.logger import get_logger
from ..llm.base import LLMProvider
from .document_processor import ProcessingResult

logger = get_logger(__name__)


class AgenticDocumentProcessor:
    """
    Agentic processor where LLM gets Paperless API as tools and decides everything.
    
    This is a revolutionary approach where the LLM:
    - Analyzes the document
    - Checks existing tags/correspondents
    - Decides which ones to use or create
    - Makes all updates autonomously
    """

    def __init__(
        self,
        paperless_client: PaperlessClient,
        llm_provider: LLMProvider,
    ) -> None:
        """
        Initialize agentic processor.

        Args:
            paperless_client: Paperless API client
            llm_provider: LLM provider instance
        """
        self.paperless = paperless_client
        self.llm = llm_provider

    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build function/tools schema for LLM."""
        return [
            {
                "name": "update_document",
                "description": "Update a document in Paperless with title, tags, correspondent, and metadata. IMPORTANT: Analyze the ENTIRE document content carefully before making decisions!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Descriptive title for the document. Format: 'Type - Key Info - Date'. Example: 'Rechnung - Laptop Dell XPS - 2025-10-06'",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of relevant tags based on ACTUAL document content (lowercase, hyphens instead of spaces). Maximum 8-10 tags. Tags must match the document's ACTUAL content, not random associations. Example: For a laptop invoice use ['rechnung', 'hardware', 'laptop', 'elektronik'], NOT ['elektromobilitaet']!",
                        },
                        "correspondent": {
                            "type": "string",
                            "description": "CRITICAL: The EXACT name of the company/person who ISSUED/CREATED/SENT this document. Look at the letterhead/logo at the TOP of the document - that's the correspondent! If the document shows 'EPC Global Solutions Deutschland GmbH' at the top/header, then correspondent MUST be 'EPC Global Solutions Deutschland GmbH'. Do NOT use companies that are only mentioned in the text (like 'Telekom' if it's just mentioned as a topic). The correspondent is the SENDER, not the subject!",
                        },
                        "document_date": {
                            "type": "string",
                            "description": "Document date in ISO format (YYYY-MM-DD)",
                        },
                        "requires_action": {
                            "type": "boolean",
                            "description": "True if document requires user action (unpaid invoice, reminder, deadline, etc.)",
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "MANDATORY detailed explanation: 1) Who is the document issuer/sender? (quote from document) 2) What is the main content/product/service? 3) Why did you choose this correspondent? 4) Why did you choose these specific tags and how do they match the actual content? 5) What important data was extracted? Be very explicit and cite evidence from the document!",
                        },
                        "custom_fields": {
                            "type": "object",
                            "description": "Custom fields with extracted data. For invoices extract: invoice_number, amount, currency, due_date, product/service description. For contracts: contract_number, start_date, end_date. Include all relevant fields you can identify.",
                            "properties": {
                                "invoice_number": {"type": "string", "description": "Invoice/bill number"},
                                "amount": {"type": "number", "description": "Total amount as number"},
                                "currency": {"type": "string", "description": "Currency code (EUR, USD, etc.)"},
                                "due_date": {"type": "string", "description": "Payment due date (YYYY-MM-DD)"},
                                "contract_number": {"type": "string", "description": "Contract/customer number"},
                                "customer_id": {"type": "string", "description": "Customer ID"},
                                "product": {"type": "string", "description": "Main product/service being billed"},
                            },
                        },
                    },
                    "required": ["title"],
                },
            }
        ]

    def _build_system_prompt(
        self,
        document_content: str,
        existing_tags: List[Tag],
        existing_correspondents: List[Correspondent],
    ) -> str:
        """Build system prompt with available context."""
        tags_list = ", ".join([tag.name for tag in existing_tags[:100]])
        corr_list = "\n".join(
            [f"  - {corr.name}" for corr in existing_correspondents[:50]]
        )

        prompt = f"""Du bist ein intelligenter Dokumenten-Verarbeitungs-Agent für Paperless-ngx.

Deine Aufgabe:
1. Analysiere das folgende Dokument SEHR SORGFÄLTIG und VOLLSTÄNDIG
2. Erstelle einen aussagekräftigen Titel
3. Wähle oder erstelle passende Tags
4. Identifiziere den KORREKTEN Correspondent/Vendor
5. Extrahiere das Dokumentdatum

KRITISCHE ANALYSE-SCHRITTE:
1. LESE DEN GESAMTEN DOKUMENTINHALT komplett durch
2. Suche nach dem ABSENDER/AUSSTELLER (Logo, Briefkopf, "Von:", Firmenstempel, Absenderadresse)
3. Identifiziere den DOKUMENTTYP (Rechnung, Vertrag, Mahnung, etc.)
4. Identifiziere den HAUPTINHALT (was wird verkauft/angeboten/behandelt?)
5. Extrahiere ALLE wichtigen Daten (Beträge, Daten, Nummern)

🔴 CORRESPONDENT - ABSOLUT KRITISCH! 🔴

DER CORRESPONDENT IST:
✅ Die Firma/Person die das Dokument ERSTELLT/AUSGESTELLT/VERSCHICKT hat
✅ Der Absender im Briefkopf / Logo oben auf dem Dokument
✅ Die Firma deren Stempel/Unterschrift auf dem Dokument ist
✅ Wer die Rechnung/Brief SCHREIBT

DER CORRESPONDENT IST NICHT:
❌ Eine Firma die nur im Text ERWÄHNT wird
❌ Der Kunde/Empfänger des Dokuments
❌ Ein Produkt-Hersteller der nur erwähnt wird

BEISPIELE:
1. Rechnung von "EPC Global Solutions" für einen "HP Laptop"
   → Correspondent = "EPC Global Solutions Deutschland GmbH" ✅
   → NICHT "Telekom" (auch wenn Telekom erwähnt wird) ❌
   → NICHT "HP" (nur Produkt-Hersteller) ❌

2. Stromrechnung von "EnBW"
   → Correspondent = "EnBW Energie Baden-Württemberg AG" ✅

3. Brief von "ARD ZDF Beitragsservice"
   → Correspondent = "ARD ZDF Deutschlandradio Beitragsservice" ✅

VORGEHENSWEISE (DU HAST VOLLE KONTROLLE!):
1. Schaue auf den BRIEFKOPF/LOGO oben im Dokument - DAS ist der Correspondent
2. Suche nach "Absender:", "Von:", Firmenstempel, Absenderadresse
3. Schreibe den EXAKTEN Firmennamen wie er im Briefkopf steht
4. Prüfe die Liste der existierenden Correspondents unten
5. WENN ein Correspondent EXAKT den gleichen Namen hat → verwende diesen
6. WENN KEIN Correspondent exakt passt → schreibe den Namen wie im Dokument und ich erstelle einen neuen
7. IGNORIERE alle anderen im Text erwähnten Firmen - die sind NICHT der Correspondent!

WICHTIG: Du entscheidest! Wenn "EPC Global Solutions Deutschland GmbH" im Briefkopf steht und du in der Liste nur "Telekom Deutschland GmbH" siehst, dann schreibe "EPC Global Solutions Deutschland GmbH" - ich erstelle dann automatisch einen neuen Correspondent mit diesem Namen!

TAGS (KRITISCH - Basierend auf TATSÄCHLICHEM Inhalt!):
- Prüfe ZUERST die existierenden Tags
- VERWENDE existierende Tags NUR wenn sie zum INHALT passen
- Erstelle NUR neue Tags wenn wirklich notwendig
- Tags müssen zum HAUPTINHALT des Dokuments passen:
  * Laptop-Rechnung → "rechnung", "hardware", "laptop", "elektronik" (NICHT "elektromobilitaet"!)
  * Stromrechnung → "rechnung", "energie", "strom"
  * Handy-Rechnung → "rechnung", "telekommunikation", "mobilfunk"
  * Auto-Rechnung → "rechnung", "fahrzeug", "auto" oder "elektromobilitaet" (wenn Elektro-Auto)
- Maximum 8-10 relevante Tags pro Dokument
- Lowercase, Bindestriche statt Leerzeichen
- KEINE generischen Tags wenn spezifische besser passen

CUSTOM FIELDS:
- Extrahiere ALLE relevanten Daten in custom_fields
- Nutze sinnvolle Feldnamen: invoice_number, amount, currency, due_date
- Füge weitere Felder hinzu wenn relevant: contract_number, customer_id, product, etc.
- Bei Rechnungen: invoice_number, amount, currency, due_date, product/service beschreibung
- Beträge als Zahlen, Daten im ISO-Format (YYYY-MM-DD)

REQUIRES_ACTION (WICHTIG!):
- Setze requires_action=true wenn das Dokument Aktion erfordert:
  * Unbezahlte Rechnungen/Invoices
  * Mahnungen/Reminders
  * Zahlungsaufforderungen
  * Dokumente mit Fälligkeitsdatum
  * Fristen/Deadlines
  * Wichtige Verträge die Unterschrift brauchen
- Setze requires_action=false für:
  * Informationsdokumente
  * Bestätigungen
  * Bereits bezahlte Rechnungen
  * Allgemeine Korrespondenz

REASONING (PFLICHT - DETAILLIERT!):
- Erkläre ALLE deine Entscheidungen ausführlich in 'reasoning'
- WER ist der Absender/Aussteller des Dokuments? (Name aus dem Dokument zitieren!)
- WARUM hast du diesen Correspondent gewählt?
- WAS ist der Hauptinhalt des Dokuments? (Produkt/Dienstleistung)
- WARUM hast du diese Tags gewählt? Wie passen sie zum Inhalt?
- Welche Tags wurden wiederverwendet? Welche neu erstellt und WARUM?
- Warum requires_action=true/false?
- Welche wichtigen Daten wurden extrahiert? (Beträge, Nummern, Daten)
- Bei Fehlentscheidungen in der Vergangenheit: KORRIGIERE sie!

Existierende Tags in Paperless:
{tags_list}

Existierende Correspondents in Paperless:
{corr_list}

Dokument-Inhalt (OCR):
{document_content}

Analysiere das Dokument und rufe die update_document Funktion auf mit deinen Entscheidungen UND reasoning."""

        return prompt

    async def process_document(self, document_id: int) -> ProcessingResult:
        """
        Process document using agentic approach - LLM decides everything.

        Args:
            document_id: Paperless document ID

        Returns:
            ProcessingResult
        """
        start_time = time.time()
        result = ProcessingResult(document_id=document_id, success=False)

        logger.info("agentic_processing_start", document_id=document_id)

        try:
            # 1. Fetch document and content
            document = await self.paperless.get_document(document_id)
            content = await self.paperless.download_document_content(document_id)

            if not content or len(content.strip()) < 10:
                raise ValueError("Document content is empty or too short")

            # 2. Check if already processed
            existing_tags = await self.paperless.get_tags()
            processed_tag = None
            for tag in existing_tags:
                if tag.name == "bp-processed":
                    processed_tag = tag
                    break

            if processed_tag and processed_tag.id in document.tags:
                logger.info(
                    "document_already_processed",
                    document_id=document_id,
                    reason="Has bp-processed tag",
                )
                result.success = True
                result.processing_time = time.time() - start_time
                return result

            # 3. Get existing correspondents for context
            existing_correspondents = await self.paperless.get_correspondents()

            # 4. Build system prompt with context
            system_prompt = self._build_system_prompt(
                document_content=content,
                existing_tags=existing_tags,
                existing_correspondents=existing_correspondents,
            )

            # 5. Get tools schema
            tools_schema = self._build_tools_schema()

            # 6. Let LLM analyze and decide
            logger.info("llm_analyzing_document", content_length=len(content))

            response = await self.llm.generate_structured_output(
                prompt=system_prompt,
                schema=tools_schema[0]["parameters"],
                temperature=0.3,  # Slightly higher for better reasoning
            )

            decisions = response.data
            logger.info("llm_decisions", decisions=decisions)
            
            # Validate reasoning exists and is detailed enough
            reasoning = decisions.get("reasoning", "")
            if not reasoning or len(reasoning) < 100:
                logger.warning(
                    "insufficient_reasoning",
                    document_id=document_id,
                    reasoning_length=len(reasoning),
                    message="LLM provided insufficient reasoning - may indicate poor analysis"
                )
            
            # Log if correspondent doesn't match any existing ones (new creation)
            correspondent_name = decisions.get("correspondent", "")
            if correspondent_name:
                existing_corr_names = [c.name.lower() for c in existing_correspondents]
                if correspondent_name.lower() not in existing_corr_names:
                    logger.info(
                        "new_correspondent_will_be_created",
                        document_id=document_id,
                        new_name=correspondent_name,
                        reason="No existing correspondent matched"
                    )

            # 7. Execute LLM's decisions
            await self._execute_llm_decisions(document_id, decisions, existing_tags, existing_correspondents)

            # 8. Mark as successful
            result.success = True
            result.title = decisions.get("title")
            result.tags = decisions.get("tags", [])
            result.correspondent = decisions.get("correspondent")
            result.metadata = {
                "document_date": decisions.get("document_date"),
                "reasoning": decisions.get("reasoning", ""),  # LLM's explanation
                "custom_fields": decisions.get("custom_fields", {}),
            }
            result.processing_time = time.time() - start_time
            result.llm_tokens_used = response.tokens_used
            result.llm_cost = response.cost

            logger.info(
                "agentic_processing_complete",
                document_id=document_id,
                duration=result.processing_time,
                tokens=result.llm_tokens_used,
                cost=result.llm_cost,
            )

            return result

        except Exception as e:
            result.errors.append(str(e))
            result.processing_time = time.time() - start_time
            logger.error(
                "agentic_processing_failed",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            return result

    async def _execute_llm_decisions(
        self,
        document_id: int,
        decisions: Dict[str, Any],
        existing_tags: List[Tag],
        existing_correspondents: List[Correspondent],
    ) -> None:
        """
        Execute the decisions made by LLM.

        Args:
            document_id: Document ID
            decisions: LLM's decisions
            existing_tags: Current tags in Paperless
            existing_correspondents: Current correspondents in Paperless
        """
        update_data: Dict[str, Any] = {}

        # 1. Set title
        if decisions.get("title"):
            update_data["title"] = decisions["title"]

        # 2. Handle tags - match existing or create new
        if decisions.get("tags"):
            tag_ids = []
            decided_tags = decisions["tags"]

            # Build map of existing tags (lowercase for matching)
            existing_tag_map = {tag.name.lower(): tag for tag in existing_tags}

            for tag_name in decided_tags:
                tag_name_lower = tag_name.lower()

                # Check if tag already exists (exact or fuzzy match)
                matched_tag = None
                if tag_name_lower in existing_tag_map:
                    matched_tag = existing_tag_map[tag_name_lower]
                    logger.debug("tag_matched", requested=tag_name, matched=matched_tag.name)
                else:
                    # Fuzzy match - check if tag is substring or vice versa
                    for existing_name, tag in existing_tag_map.items():
                        if tag_name_lower in existing_name or existing_name in tag_name_lower:
                            matched_tag = tag
                            logger.debug(
                                "tag_fuzzy_matched",
                                requested=tag_name,
                                matched=matched_tag.name,
                            )
                            break

                if matched_tag:
                    tag_ids.append(matched_tag.id)
                else:
                    # Create new tag
                    try:
                        new_tag = await self.paperless.create_tag(tag_name)
                        tag_ids.append(new_tag.id)
                        logger.info("tag_created", name=tag_name, id=new_tag.id)
                    except Exception as e:
                        logger.warning("tag_creation_failed", tag_name=tag_name, error=str(e))

            # Add action-required tag if needed (RED for attention!)
            if decisions.get("requires_action", False):
                try:
                    action_tag = existing_tag_map.get("offen")
                    if not action_tag:
                        # Use get_or_create to avoid duplicate creation errors
                        action_tag = await self.paperless.get_or_create_tag(
                            "offen", color="#e74c3c"  # RED color for attention!
                        )
                        existing_tag_map["offen"] = action_tag
                    tag_ids.append(action_tag.id)
                    logger.info("action_required_tag_added", document_id=document_id)
                except Exception as e:
                    logger.warning(
                        "action_tag_creation_failed",
                        document_id=document_id,
                        error=str(e),
                        message="Skipping 'offen' tag due to creation error"
                    )

            # Add bp-processed tag
            try:
                processed_tag = existing_tag_map.get("bp-processed")
                if not processed_tag:
                    # Use get_or_create to avoid duplicate creation errors
                    processed_tag = await self.paperless.get_or_create_tag(
                        "bp-processed", color="#2ecc71"  # GREEN for processed
                    )
                tag_ids.append(processed_tag.id)
            except Exception as e:
                logger.warning(
                    "processed_tag_creation_failed",
                    document_id=document_id,
                    error=str(e),
                    message="Skipping 'bp-processed' tag due to creation error"
                )

            update_data["tags"] = tag_ids

        # 3. Handle correspondent - LLM has full control, only exact match or create new
        if decisions.get("correspondent"):
            correspondent_name = decisions["correspondent"]

            # Build map of existing correspondents (lowercase for matching)
            existing_corr_map = {
                corr.name.lower(): corr for corr in existing_correspondents
            }

            matched_corr = None

            # ONLY exact match (case-insensitive)
            # LLM decides whether to use existing or create new
            if correspondent_name.lower() in existing_corr_map:
                matched_corr = existing_corr_map[correspondent_name.lower()]
                logger.info(
                    "correspondent_exact_match",
                    requested=correspondent_name,
                    matched=matched_corr.name,
                    llm_decision="LLM chose to use existing correspondent"
                )
                update_data["correspondent"] = matched_corr.id
            else:
                # No exact match - create new correspondent as LLM decided
                try:
                    new_corr = await self.paperless.create_correspondent(correspondent_name)
                    update_data["correspondent"] = new_corr.id
                    logger.info(
                        "correspondent_created",
                        name=correspondent_name,
                        id=new_corr.id,
                        llm_decision="LLM chose to create new correspondent"
                    )
                except Exception as e:
                    logger.warning(
                        "correspondent_creation_failed",
                        name=correspondent_name,
                        error=str(e),
                    )

        # 4. Set document date
        if decisions.get("document_date"):
            update_data["created_date"] = decisions["document_date"]

        # 5. Custom fields are logged but not sent to API (Paperless may not support them)
        if decisions.get("custom_fields"):
            logger.info("custom_fields_extracted", fields=decisions["custom_fields"])

        # 6. Execute update
        if update_data:
            await self.paperless.update_document(document_id, **update_data)
            logger.info("document_updated", document_id=document_id, updates=update_data)