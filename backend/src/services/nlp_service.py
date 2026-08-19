"""
NLP Service — Named entity recognition and information extraction.

Implements Phase 3 functionality:
- Entity extraction using spaCy + OpenNyAI
- Legal section detection
- Timeline extraction
"""


class NLPService:
    """Handles NLP processing of legal document text."""

    def __init__(self):
        self._nlp_model = None  # Lazy-loaded spaCy model

    async def extract_entities(self, text: str, document_id: str) -> list[dict]:
        """
        Extract named entities from document text.

        Uses spaCy + OpenNyAI legal NER model to identify:
        PETITIONER, RESPONDENT, JUDGE, COURT, STATUTE, PROVISION, DATE, etc.

        Args:
            text: Extracted document text.
            document_id: ID of the source document (for traceability).

        Returns:
            List of entity dicts: {entity_type, entity_text, start_char, end_char, source_sentence}
        """
        # TODO (Phase 3): Implement spaCy NER pipeline
        raise NotImplementedError("NER extraction will be implemented in Phase 3")

    async def extract_legal_sections(self, text: str) -> list[dict]:
        """
        Detect references to legal sections (BNS, IPC, CrPC, etc.).

        Uses EntityRuler patterns + regex for section detection.

        Args:
            text: Document text.

        Returns:
            List of section dicts: {section_number, statute, full_reference, context}
        """
        # TODO (Phase 3): Implement section extraction
        raise NotImplementedError("Section extraction will be implemented in Phase 3")

    async def extract_timeline(self, text: str) -> list[dict]:
        """
        Extract date-event pairs to build a case timeline.

        Args:
            text: Document text.

        Returns:
            List of timeline entries: {date, event_description, source_page}
        """
        # TODO (Phase 3): Implement timeline extraction
        raise NotImplementedError("Timeline extraction will be implemented in Phase 3")


# Singleton instance
nlp_service = NLPService()
