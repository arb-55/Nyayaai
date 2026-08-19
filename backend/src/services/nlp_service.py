"""
NLP Service — Named entity recognition and information extraction.

Implements Phase 3A:
- Controlled legal entity extraction using Gemini LLM adapter
- Safe structured JSON validation and error handling
"""

import logging

from src.agents.prompts.entity_extraction import (
    ENTITY_EXTRACTION_SYSTEM_INSTRUCTION,
    build_entity_extraction_prompt,
)
from src.llm.adapter import llm_adapter

logger = logging.getLogger(__name__)

CONTROLLED_ENTITY_TYPES = {
    "PERSON",
    "ORGANIZATION",
    "LOCATION",
    "DATE",
    "CASE_NUMBER",
    "POLICE_STATION",
    "LEGAL_SECTION",
    "COURT",
    "JUDGE",
    "ADVOCATE",
    "MONEY_AMOUNT",
}


class NLPService:
    """Handles NLP processing and entity extraction from legal documents."""

    async def extract_entities(self, text: str, filename: str = "document.pdf") -> list[dict]:
        """
        Extract legal named entities from document text using Gemini LLM adapter.

        Args:
            text: Cleaned document text string.
            filename: Original document filename for prompt context.

        Returns:
            List of validated entity dicts:
            [
              {
                "entity_type": str,
                "entity_text": str,
                "normalized_value": str | None,
                "confidence": float,
                "page_number": int | None,
                "source_sentence": str | None
              }
            ]
        """
        if not text or not text.strip():
            logger.info("Empty text provided for entity extraction. Skipping LLM call.")
            return []

        prompt = build_entity_extraction_prompt(document_text=text, filename=filename)

        try:
            raw_result = await llm_adapter.generate_json(
                prompt=prompt,
                system_instruction=ENTITY_EXTRACTION_SYSTEM_INSTRUCTION,
                temperature=0.1,  # Low temperature for factual extraction
            )
        except Exception as err:
            logger.error(f"Entity extraction LLM call failed for '{filename}': {err}")
            return []

        if not isinstance(raw_result, dict):
            logger.warning(f"LLM returned non-dict response for '{filename}': {raw_result}")
            return []

        raw_entities = raw_result.get("entities", [])
        if not isinstance(raw_entities, list):
            logger.warning(f"LLM 'entities' field is not a list for '{filename}': {raw_entities}")
            return []

        validated_entities = []
        for item in raw_entities:
            if not isinstance(item, dict):
                continue

            entity_type = str(item.get("entity_type", "")).strip().upper()
            entity_text = str(item.get("entity_text", "")).strip()

            if not entity_text:
                continue

            # Fallback mapping for common synonym types if needed
            if entity_type not in CONTROLLED_ENTITY_TYPES:
                if "SECTION" in entity_type or "PROVISION" in entity_type or "STATUTE" in entity_type:
                    entity_type = "LEGAL_SECTION"
                elif "ACCUSED" in entity_type or "VICTIM" in entity_type or "WITNESS" in entity_type or "PETITIONER" in entity_type:
                    entity_type = "PERSON"
                elif "ADDRESS" in entity_type or "CITY" in entity_type:
                    entity_type = "LOCATION"
                else:
                    # Skip unmapped non-standard entity types
                    continue

            norm_val = item.get("normalized_value")
            normalized_value = str(norm_val).strip() if norm_val is not None else entity_text

            try:
                conf = float(item.get("confidence", 0.9))
                confidence = max(0.0, min(1.0, conf))
            except (ValueError, TypeError):
                confidence = 0.9

            page_num = item.get("page_number")
            page_number = int(page_num) if isinstance(page_num, int) or (isinstance(page_num, str) and page_num.isdigit()) else None

            source_sent = item.get("source_sentence")
            source_sentence = str(source_sent).strip() if source_sent else None

            validated_entities.append({
                "entity_type": entity_type,
                "entity_text": entity_text,
                "normalized_value": normalized_value,
                "confidence": confidence,
                "page_number": page_number,
                "source_sentence": source_sentence,
            })

        logger.info(f"Successfully extracted {len(validated_entities)} entities from '{filename}'.")
        return validated_entities


# Singleton instance
nlp_service = NLPService()
