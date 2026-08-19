"""
Evidence Agent — Extracts factual evidence statements from document text.

Implements Phase 3B:
- Analyzes document text using Gemini LLM adapter
- Identifies factual evidence statements, categories, excerpts, and confidence
- Preserves strict source traceability
"""

import logging

from src.agents.prompts.evidence_extraction import (
    EVIDENCE_EXTRACTION_SYSTEM_INSTRUCTION,
    build_evidence_extraction_prompt,
)
from src.llm.adapter import llm_adapter

logger = logging.getLogger(__name__)

CONTROLLED_CATEGORIES = {
    "FACT",
    "TESTIMONY",
    "DOCUMENTARY",
    "PHYSICAL",
    "DIGITAL",
    "FINANCIAL",
    "MEDICAL",
    "OTHER",
}

CONTROLLED_STRENGTH = {"HIGH", "MEDIUM", "LOW"}


class EvidenceAgent:
    """Agent responsible for analyzing document text and extracting evidence statements."""

    async def extract_evidence(
        self, text: str, document_id: str, filename: str = "document.pdf"
    ) -> list[dict]:
        """
        Extract factual evidence statements from document text.

        Args:
            text: Cleaned document text string.
            document_id: UUID string of the source document for traceability.
            filename: Original document filename for prompt context.

        Returns:
            List of evidence dicts:
            [
              {
                "category": str,
                "statement": str,
                "source_text": str,
                "confidence": float,
                "evidence_strength": str,
                "page_number": int | None,
                "document_id": str
              }
            ]
        """
        if not text or not text.strip():
            logger.info("Empty text provided for evidence extraction. Skipping LLM call.")
            return []

        prompt = build_evidence_extraction_prompt(document_text=text, filename=filename)

        try:
            raw_result = await llm_adapter.generate_json(
                prompt=prompt,
                system_instruction=EVIDENCE_EXTRACTION_SYSTEM_INSTRUCTION,
                temperature=0.1,  # Low temperature for factual consistency
            )
        except Exception as err:
            logger.error(f"Evidence extraction LLM call failed for '{filename}': {err}")
            return []

        if not isinstance(raw_result, dict):
            logger.warning(f"LLM returned non-dict response for evidence '{filename}': {raw_result}")
            return []

        raw_evidence = raw_result.get("evidence", [])
        if not isinstance(raw_evidence, list):
            logger.warning(f"LLM 'evidence' field is not a list for '{filename}': {raw_evidence}")
            return []

        validated_evidence = []
        for item in raw_evidence:
            if not isinstance(item, dict):
                continue

            category = str(item.get("category", "")).strip().upper()
            statement = str(item.get("statement", "")).strip()
            source_text = str(item.get("source_text", "")).strip()

            if not statement:
                continue

            if category not in CONTROLLED_CATEGORIES:
                category = "FACT"

            strength = str(item.get("evidence_strength", "HIGH")).strip().upper()
            if strength not in CONTROLLED_STRENGTH:
                strength = "HIGH"

            try:
                conf = float(item.get("confidence", 0.9))
                confidence = max(0.0, min(1.0, conf))
            except (ValueError, TypeError):
                confidence = 0.9

            page_num = item.get("page_number")
            page_number = (
                int(page_num)
                if isinstance(page_num, int) or (isinstance(page_num, str) and page_num.isdigit())
                else None
            )

            validated_evidence.append({
                "category": category,
                "statement": statement,
                "source_text": source_text or statement,
                "confidence": confidence,
                "evidence_strength": strength,
                "page_number": page_number,
                "document_id": str(document_id),
            })

        logger.info(f"Successfully extracted {len(validated_evidence)} evidence statements from '{filename}'.")
        return validated_evidence


# Singleton instance
evidence_agent = EvidenceAgent()
