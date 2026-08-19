"""
Contradiction Agent — Identifies potential factual inconsistencies between case documents.

Implements Phase 3C:
- Lightweight candidate selection based on shared entities, dates, times, or evidence categories
- Gemini LLM analysis comparing candidate statement pairs
- Strict persistence filtering (CONTRADICTION only with confidence >= 0.6)
- Traceability preserving both Source A and Source B references
"""

import logging
import re
from typing import Any

from src.agents.prompts.contradiction_detection import (
    CONTRADICTION_DETECTION_SYSTEM_INSTRUCTION,
    build_contradiction_prompt,
)
from src.llm.adapter import llm_adapter

logger = logging.getLogger(__name__)

# Minimum confidence score required to persist a contradiction finding
MIN_CONTRADICTION_CONFIDENCE = 0.6

CONTROLLED_CONTRADICTION_TYPES = {
    "TIME_CONFLICT",
    "DATE_CONFLICT",
    "LOCATION_CONFLICT",
    "PERSON_PRESENCE_CONFLICT",
    "IDENTITY_CONFLICT",
    "AMOUNT_CONFLICT",
    "EVENT_DESCRIPTION_CONFLICT",
    "OBJECT_ATTRIBUTE_CONFLICT",
    "OTHER",
}


def select_candidate_pairs(evidence_findings: list[dict], entities: list[dict]) -> list[tuple[dict, dict]]:
    """
    Select candidate statement pairs from different documents that share factual anchors.

    Args:
        evidence_findings: List of evidence dicts or dict representations of AgentFinding.
        entities: List of extracted entity dicts.

    Returns:
        List of tuples: [(finding_a, finding_b)]
    """
    if len(evidence_findings) < 2:
        return []

    # Map entities to document IDs and entity texts
    entity_texts_by_doc = {}
    for ent in entities:
        doc_id = str(ent.get("document_id") or "")
        text = str(ent.get("entity_text") or "").strip().lower()
        if doc_id and text:
            entity_texts_by_doc.setdefault(doc_id, set()).add(text)

    candidate_pairs = []
    seen_pairs = set()

    for i in range(len(evidence_findings)):
        for j in range(i + 1, len(evidence_findings)):
            fa = evidence_findings[i]
            fb = evidence_findings[j]

            refs_a = fa.get("source_references") or fa
            refs_b = fb.get("source_references") or fb

            doc_a = str(refs_a.get("document_id") or "")
            doc_b = str(refs_b.get("document_id") or "")

            # Only compare statements from DIFFERENT documents
            if not doc_a or not doc_b or doc_a == doc_b:
                continue

            pair_key = tuple(sorted([str(fa.get("id") or i), str(fb.get("id") or j)]))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            stmt_a = str(fa.get("finding_text") or refs_a.get("statement") or "").strip()
            stmt_b = str(fb.get("finding_text") or refs_b.get("statement") or "").strip()

            if not stmt_a or not stmt_b:
                continue

            cat_a = refs_a.get("category", "FACT")
            cat_b = refs_b.get("category", "FACT")

            # Check matching anchors: shared entities, shared numbers/times, or matching categories
            ents_a = entity_texts_by_doc.get(doc_a, set())
            ents_b = entity_texts_by_doc.get(doc_b, set())
            shared_ents = ents_a.intersection(ents_b)

            has_numerical_a = bool(re.search(r'\d+', stmt_a))
            has_numerical_b = bool(re.search(r'\d+', stmt_b))

            is_same_category = (cat_a == cat_b)

            # Accept as candidate pair if they share entities, numerical figures, or category
            if shared_ents or (has_numerical_a and has_numerical_b) or is_same_category:
                candidate_pairs.append((fa, fb))

            # Limit candidate pairs to prevent excessive LLM calls
            if len(candidate_pairs) >= 10:
                break
        if len(candidate_pairs) >= 10:
            break

    return candidate_pairs


class ContradictionAgent:
    """Agent responsible for analyzing statement pairs and identifying factual contradictions."""

    async def analyze_candidate_pairs(
        self, candidate_pairs: list[tuple[dict, dict]]
    ) -> list[dict]:
        """
        Analyze candidate statement pairs via Gemini LLM to detect factual contradictions.

        Args:
            candidate_pairs: List of (finding_a, finding_b) tuples.

        Returns:
            List of validated contradiction dicts containing both source_a and source_b.
        """
        validated_contradictions = []

        for fa, fb in candidate_pairs:
            refs_a = fa.get("source_references") or fa
            refs_b = fb.get("source_references") or fb

            stmt_a = str(fa.get("finding_text") or refs_a.get("statement") or "").strip()
            stmt_b = str(fb.get("finding_text") or refs_b.get("statement") or "").strip()

            doc_a_name = str(refs_a.get("document_name") or "Document A")
            doc_b_name = str(refs_b.get("document_name") or "Document B")

            prompt = build_contradiction_prompt(
                statement_a=stmt_a,
                source_a_name=doc_a_name,
                statement_b=stmt_b,
                source_b_name=doc_b_name,
            )

            try:
                raw_result = await llm_adapter.generate_json(
                    prompt=prompt,
                    system_instruction=CONTRADICTION_DETECTION_SYSTEM_INSTRUCTION,
                    temperature=0.1,  # Low temperature for factual consistency
                )
            except Exception as err:
                logger.error(f"Contradiction detection LLM call failed for pair: {err}")
                continue

            if not isinstance(raw_result, dict):
                continue

            classification = str(raw_result.get("classification", "")).strip().upper()
            if classification != "CONTRADICTION":
                # Do NOT persist POSSIBLY_COMPATIBLE or INSUFFICIENT_INFORMATION
                continue

            try:
                conf = float(raw_result.get("confidence", 0.0))
                confidence = max(0.0, min(1.0, conf))
            except (ValueError, TypeError):
                confidence = 0.0

            # Strictly enforce confidence >= MIN_CONTRADICTION_CONFIDENCE (0.6)
            if confidence < MIN_CONTRADICTION_CONFIDENCE:
                logger.info(f"Skipping contradiction with confidence {confidence} < {MIN_CONTRADICTION_CONFIDENCE}")
                continue

            ctype = str(raw_result.get("contradiction_type", "OTHER")).strip().upper()
            if ctype not in CONTROLLED_CONTRADICTION_TYPES:
                ctype = "OTHER"

            explanation = str(raw_result.get("explanation", "")).strip()
            if not explanation:
                explanation = f"Potential contradiction between {doc_a_name} and {doc_b_name}."

            source_a_data = {
                "document_id": str(refs_a.get("document_id") or ""),
                "document_name": doc_a_name,
                "page_number": refs_a.get("page_number"),
                "statement": stmt_a,
                "excerpt": str(refs_a.get("excerpt") or refs_a.get("source_text") or stmt_a),
            }

            source_b_data = {
                "document_id": str(refs_b.get("document_id") or ""),
                "document_name": doc_b_name,
                "page_number": refs_b.get("page_number"),
                "statement": stmt_b,
                "excerpt": str(refs_b.get("excerpt") or refs_b.get("source_text") or stmt_b),
            }

            # Enforce that BOTH source_a and source_b exist and are populated
            if not source_a_data["document_id"] or not source_b_data["document_id"]:
                continue

            validated_contradictions.append({
                "classification": "CONTRADICTION",
                "contradiction_type": ctype,
                "explanation": explanation,
                "confidence": confidence,
                "source_a": source_a_data,
                "source_b": source_b_data,
            })

        logger.info(f"Detected {len(validated_contradictions)} valid contradictions across candidate pairs.")
        return validated_contradictions


# Singleton instance
contradiction_agent = ContradictionAgent()
