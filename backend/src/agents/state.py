"""
Agent State — Shared state schema for the LangGraph multi-agent graph.

This TypedDict defines the data that flows between all agent nodes.
"""

from typing import TypedDict


class CaseAnalysisState(TypedDict, total=False):
    """
    Shared state for the LangGraph agent workflow.

    Fields are populated progressively as agents complete their work:
    1. Orchestrator populates case_id, documents, entities, timeline
    2. Each agent populates its findings field
    3. Consensus engine populates consensus_report and overall_confidence
    """

    # ── Input (set by orchestrator) ──
    case_id: str
    documents: list[dict]       # [{id, filename, type, text, page_count}]
    entities: list[dict]        # [{entity_type, entity_text, document_id, ...}]
    timeline: list[dict]        # [{date, event_description, source_document}]
    legal_sections: list[dict]  # [{section_number, statute, full_reference}]

    # ── Agent outputs (set by individual agents) ──
    evidence_findings: list[dict] | None
    contradiction_findings: list[dict] | None
    legal_findings: list[dict] | None

    # ── Consensus output (set by consensus engine) ──
    consensus_report: dict | None
    overall_confidence: float | None

    # ── Error tracking ──
    errors: list[str]
