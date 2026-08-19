"""
Legal Research Agent — Formulates research questions and retrieves source-backed legal authorities.

Implements Phase 3D:
- Generates focused legal research questions from case context using Gemini LLM adapter
- Retrieves legal authorities via LegalRetrievalService
- Applies strict 2-level source verification (Domain Verification + Content Verification)
- Preserves source traceability without URL/citation fabrication
"""

import logging

from src.agents.prompts.legal_research import (
    LEGAL_RESEARCH_SYSTEM_INSTRUCTION,
    build_legal_research_prompt,
)
from src.llm.adapter import llm_adapter
from src.services.legal_retrieval_service import legal_retrieval_service

logger = logging.getLogger(__name__)

CONTROLLED_AUTHORITY_TYPES = {
    "STATUTE",
    "CASE_LAW",
    "RULE",
    "REGULATION",
    "CONSTITUTIONAL_PROVISION",
    "OTHER",
}


class LegalResearchAgent:
    """Agent responsible for conducting AI-assisted legal research based on case context."""

    async def conduct_research(self, context_text: str) -> list[dict]:
        """
        Formulate legal research questions and retrieve verified/unverified legal authorities.

        Args:
            context_text: Summary context string containing entities, evidence, and contradictions.

        Returns:
            List of legal research finding dicts:
            [
              {
                "research_question": str,
                "authority_type": str,
                "title": str,
                "citation": str,
                "legal_proposition": str,
                "source_name": str,
                "source_url": str | None,
                "verification_status": "VERIFIED" | "UNVERIFIED",
                "confidence": float
              }
            ]
        """
        if not context_text or not context_text.strip():
            logger.info("Empty context provided for legal research. Skipping LLM call.")
            return []

        prompt = build_legal_research_prompt(context_text=context_text)

        try:
            raw_result = await llm_adapter.generate_json(
                prompt=prompt,
                system_instruction=LEGAL_RESEARCH_SYSTEM_INSTRUCTION,
                temperature=0.1,  # Low temperature for factual research
            )
        except Exception as err:
            logger.error(f"Legal research LLM call failed: {err}")
            return []

        if not isinstance(raw_result, dict):
            logger.warning(f"LLM returned non-dict response for legal research: {raw_result}")
            return []

        raw_items = raw_result.get("research_results", [])
        if not isinstance(raw_items, list):
            logger.warning(f"LLM 'research_results' field is not a list: {raw_items}")
            return []

        validated_findings = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            question = str(item.get("research_question", "")).strip()
            if not question:
                continue

            atype = str(item.get("authority_type", "STATUTE")).strip().upper()
            if atype not in CONTROLLED_AUTHORITY_TYPES:
                atype = "STATUTE"
            item["authority_type"] = atype

            # Perform 2-Level Source Verification
            verified_result = await legal_retrieval_service.retrieve_and_verify(
                research_question=question,
                suggested_item=item,
            )

            validated_findings.append(verified_result)

        logger.info(f"Successfully generated {len(validated_findings)} legal research findings.")
        return validated_findings


# Singleton instance
legal_research_agent = LegalResearchAgent()
