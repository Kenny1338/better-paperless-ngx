"""Prompt templates for LLM operations."""

from typing import Dict, List, Optional


class PromptTemplates:
    """Collection of prompt templates for document processing."""

    @staticmethod
    def title_generation(
        content: str,
        tags: Optional[List[str]] = None,
        document_type: Optional[str] = None,
        language: str = "en",
    ) -> str:
        """
        Generate prompt for document title generation.

        Args:
            content: Document content
            tags: Existing tags
            document_type: Document type
            language: Document language

        Returns:
            Formatted prompt
        """
        tags_info = f"\nExisting tags: {', '.join(tags)}" if tags else ""
        type_info = f"\nDocument type: {document_type}" if document_type else ""

        if language == "de":
            return f"""Du bist ein Dokumentenverwaltungsassistent. Erstelle einen prägnanten, beschreibenden Titel für das folgende Dokument.

Der Titel sollte:
- Klar und spezifisch sein
- Wichtige Informationen enthalten (Datum, Absender, Typ)
- Unter 100 Zeichen lang sein
- Diesem Muster folgen, falls anwendbar: "Typ - Hauptinformation - Datum"

Dokumentinhalt:
{content[:2000]}{tags_info}{type_info}

Erstelle NUR den Titel, nichts anderes. Keine Anführungszeichen, keine Erklärungen."""

        return f"""You are a document management assistant. Generate a concise, descriptive title for the following document.

The title should:
- Be clear and specific
- Include key information (date, sender, type)
- Be under 100 characters
- Follow this pattern when applicable: "Type - Key Info - Date"

Document content:
{content[:2000]}{tags_info}{type_info}

Generate ONLY the title, nothing else. No quotes, no explanations."""

    @staticmethod
    def tag_generation(
        content: str,
        existing_tags: Optional[List[str]] = None,
        max_tags: int = 10,
        language: str = "en",
    ) -> str:
        """
        Generate prompt for tag generation.

        Args:
            content: Document content
            existing_tags: List of existing tags in system
            max_tags: Maximum number of tags to generate
            language: Document language

        Returns:
            Formatted prompt
        """
        existing_info = ""
        if existing_tags:
            existing_info = f"\n\nExisting tags in system: {', '.join(existing_tags[:50])}"

        if language == "de":
            return f"""Analysiere das folgende Dokument und schlage passende Tags vor.

Regeln:
- Maximal {max_tags} Tags
- Tags sollten kurz sein (1-3 Wörter)
- Verwende Kleinbuchstaben
- Verwende Bindestriche statt Leerzeichen
- Bevorzuge existierende Tags, wenn passend
- Erstelle neue Tags nur wenn notwendig

Dokumentinhalt:
{content[:3000]}{existing_info}

Gebe die Tags als kommaseparierte Liste zurück. NUR die Tags, keine Erklärungen."""

        return f"""Analyze the following document and suggest appropriate tags.

Rules:
- Maximum {max_tags} tags
- Tags should be concise (1-3 words)
- Use lowercase
- Use hyphens instead of spaces
- Prefer existing tags when applicable
- Create new tags only when necessary

Document content:
{content[:3000]}{existing_info}

Return tags as a comma-separated list. ONLY the tags, no explanations."""

    @staticmethod
    def metadata_extraction(content: str, language: str = "en") -> str:
        """
        Generate prompt for metadata extraction.

        Args:
            content: Document content
            language: Document language

        Returns:
            Formatted prompt with JSON schema
        """
        if language == "de":
            return f"""Extrahiere die folgenden Metadaten aus dem Dokument:

- document_date: Das Hauptdatum des Dokuments (ISO format YYYY-MM-DD)
- correspondent: Name des Absenders/Korrespondenten
- amount: Betrag (wenn vorhanden, als Zahl)
- currency: Währung (wenn vorhanden, z.B. EUR, USD)
- invoice_number: Rechnungsnummer (wenn vorhanden)
- due_date: Fälligkeitsdatum (wenn vorhanden, ISO format)

Dokumentinhalt:
{content[:3000]}

Gebe die Daten als JSON zurück. Verwende null für fehlende Werte."""

        return f"""Extract the following metadata from the document:

- document_date: The main date of the document (ISO format YYYY-MM-DD)
- correspondent: Name of sender/correspondent
- amount: Amount (if present, as number)
- currency: Currency (if present, e.g., EUR, USD)
- invoice_number: Invoice number (if present)
- due_date: Due date (if present, ISO format)

Document content:
{content[:3000]}

Return the data as JSON. Use null for missing values."""

    @staticmethod
    def categorization(
        content: str,
        available_types: List[str],
        language: str = "en",
    ) -> str:
        """
        Generate prompt for document categorization.

        Args:
            content: Document content
            available_types: List of available document types
            language: Document language

        Returns:
            Formatted prompt
        """
        types_list = ", ".join(available_types) if available_types else "invoice, receipt, contract, statement, letter, other"

        if language == "de":
            return f"""Kategorisiere das folgende Dokument in einen der folgenden Typen:
{types_list}

Wenn keiner passt, schlage einen neuen, passenden Typ vor.

Dokumentinhalt:
{content[:2000]}

Gebe NUR den Dokumenttyp zurück, nichts anderes."""

        return f"""Categorize the following document into one of these types:
{types_list}

If none fit, suggest a new appropriate type.

Document content:
{content[:2000]}

Return ONLY the document type, nothing else."""

    @staticmethod
    def summarization(
        content: str,
        max_length: int = 500,
        style: str = "concise",
        language: str = "en",
    ) -> str:
        """
        Generate prompt for document summarization.

        Args:
            content: Document content
            max_length: Maximum summary length
            style: Summary style (concise, detailed, bullet_points)
            language: Document language

        Returns:
            Formatted prompt
        """
        style_instructions = {
            "concise": "a brief, concise summary",
            "detailed": "a detailed summary covering all important points",
            "bullet_points": "a summary in bullet point format",
        }

        style_de = {
            "concise": "eine kurze, prägnante Zusammenfassung",
            "detailed": "eine detaillierte Zusammenfassung aller wichtigen Punkte",
            "bullet_points": "eine Zusammenfassung in Stichpunkten",
        }

        if language == "de":
            instruction = style_de.get(style, style_de["concise"])
            return f"""Erstelle {instruction} des folgenden Dokuments.

Maximal {max_length} Zeichen.

Dokumentinhalt:
{content}

Zusammenfassung:"""

        instruction = style_instructions.get(style, style_instructions["concise"])
        return f"""Create {instruction} of the following document.

Maximum {max_length} characters.

Document content:
{content}

Summary:"""

    @staticmethod
    def create_structured_schema(fields: List[str]) -> Dict:
        """
        Create JSON schema for structured output.

        Args:
            fields: List of field names to extract

        Returns:
            JSON schema
        """
        properties = {}
        for field in fields:
            if "date" in field.lower():
                properties[field] = {"type": "string", "format": "date"}
            elif "amount" in field.lower():
                properties[field] = {"type": "number"}
            else:
                properties[field] = {"type": "string"}

        return {
            "type": "object",
            "properties": properties,
            "required": [],
        }