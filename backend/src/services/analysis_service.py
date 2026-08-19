"""
Analysis Service — Orchestrates Phase 3A Entity Extraction, Phase 3B Evidence Extraction, Phase 3C Contradiction Detection, and Phase 3D Legal Research.

Implements:
- Phase 3A: Legal Entity Extraction via NLPService / Gemini LLM
- Phase 3B: Factual Evidence Extraction via EvidenceAgent / Gemini LLM
- Phase 3C: Contradiction Detection via ContradictionAgent / Gemini LLM
- Phase 3D: Legal Research Agent via LegalResearchAgent / LegalRetrievalService
- Idempotent re-run behavior per case for all agents
- Strict 2-level source verification (Domain Verification + Content Verification)
- Traceability back to source documents and official legal citations
"""

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.contradiction_agent import contradiction_agent, select_candidate_pairs
from src.agents.evidence_agent import evidence_agent
from src.agents.legal_research_agent import legal_research_agent
from src.models.analysis import Analysis, AnalysisStatus
from src.models.case import Case, CaseStatus
from src.models.document import Document
from src.models.entity import ExtractedEntity
from src.models.finding import AgentFinding, AgentType
from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.entity_repo import EntityRepository
from src.services.nlp_service import nlp_service

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates Phase 3A, Phase 3B, Phase 3C, and Phase 3D analysis pipeline."""

    async def run_analysis(self, case_id: UUID, db: AsyncSession) -> dict:
        """
        Execute full Phase 3 (3A, 3B, 3C, 3D) analysis for a case.

        Args:
            case_id: UUID of the Case.
            db: AsyncSession database session.

        Returns:
            dict containing:
                - analysis: Analysis model instance
                - entities: List of ExtractedEntity instances
                - evidence_findings: List of AgentFinding instances (EVIDENCE)
                - contradiction_findings: List of AgentFinding instances (CONTRADICTION)
                - legal_research_findings: List of AgentFinding instances (LEGAL_RESEARCH)
        """
        # 1. Fetch case
        case = await db.get(Case, case_id)
        if not case:
            raise ValueError(f"Case not found: {case_id}")

        # 2. Fetch documents for case
        stmt = select(Document).where(Document.case_id == case_id)
        result = await db.execute(stmt)
        documents = list(result.scalars().all())

        # Filter documents with usable text
        valid_docs = [
            d
            for d in documents
            if (d.cleaned_text and d.cleaned_text.strip())
            or (d.extracted_text and d.extracted_text.strip())
        ]

        # 3. Create Analysis record
        analysis = Analysis(
            case_id=case_id,
            status=AnalysisStatus.EXTRACTING_ENTITIES,
        )
        db.add(analysis)
        await db.flush()

        if not valid_docs:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = (
                "No documents with extractable text found in this case. Upload a PDF document first."
            )
            await db.commit()
            return {
                "analysis": analysis,
                "entities": [],
                "evidence_findings": [],
                "contradiction_findings": [],
                "legal_research_findings": [],
                "message": "No documents with extractable text found.",
            }

        case.status = CaseStatus.ANALYZING
        await db.flush()

        # ── Phase 3A: Entity Extraction ──
        entity_repo = EntityRepository(db)
        await entity_repo.delete_by_case(case_id)

        all_created_entities = []
        for doc in valid_docs:
            text_to_process = doc.cleaned_text or doc.extracted_text
            extracted_data = await nlp_service.extract_entities(
                text=text_to_process,
                filename=doc.filename,
            )

            doc_entities = []
            for item in extracted_data:
                entity_obj = ExtractedEntity(
                    document_id=doc.id,
                    entity_type=item["entity_type"],
                    entity_text=item["entity_text"],
                    normalized_value=item.get("normalized_value"),
                    confidence=item.get("confidence", 0.9),
                    page_number=item.get("page_number"),
                    source_sentence=item.get("source_sentence"),
                )
                doc_entities.append(entity_obj)

            if doc_entities:
                await entity_repo.bulk_create(doc_entities)
                all_created_entities.extend(doc_entities)

        # ── Phase 3B: Evidence Extraction ──
        analysis.status = AnalysisStatus.RUNNING_AGENTS
        await db.flush()

        analysis_repo = AnalysisRepository(db)
        await analysis_repo.delete_evidence_findings_by_case(case_id)

        all_evidence_findings = []
        evidence_dicts_for_candidates = []

        for doc in valid_docs:
            text_to_process = doc.cleaned_text or doc.extracted_text
            evidence_data = await evidence_agent.extract_evidence(
                text=text_to_process,
                document_id=str(doc.id),
                filename=doc.filename,
            )

            for item in evidence_data:
                finding_obj = await analysis_repo.add_finding(
                    analysis_id=analysis.id,
                    agent_type=AgentType.EVIDENCE,
                    finding_text=item["statement"],
                    confidence_score=item["confidence"],
                    source_references={
                        "document_id": str(doc.id),
                        "document_name": doc.filename,
                        "page_number": item.get("page_number"),
                        "excerpt": item.get("source_text"),
                        "category": item.get("category", "FACT"),
                        "evidence_strength": item.get("evidence_strength", "HIGH"),
                    },
                    raw_llm_response=item,
                )
                all_evidence_findings.append(finding_obj)
                evidence_dicts_for_candidates.append({
                    "id": str(finding_obj.id),
                    "finding_text": item["statement"],
                    "source_references": {
                        "document_id": str(doc.id),
                        "document_name": doc.filename,
                        "page_number": item.get("page_number"),
                        "excerpt": item.get("source_text"),
                        "category": item.get("category", "FACT"),
                        "evidence_strength": item.get("evidence_strength", "HIGH"),
                    },
                })

        # ── Phase 3C: Contradiction Detection ──
        await analysis_repo.delete_contradiction_findings_by_case(case_id)

        entity_dicts_for_candidates = [
            {
                "document_id": str(e.document_id),
                "entity_text": e.entity_text,
                "entity_type": e.entity_type,
            }
            for e in all_created_entities
        ]

        candidate_pairs = select_candidate_pairs(
            evidence_findings=evidence_dicts_for_candidates,
            entities=entity_dicts_for_candidates,
        )

        all_contradiction_findings = []
        if candidate_pairs:
            detected_contradictions = await contradiction_agent.analyze_candidate_pairs(candidate_pairs)

            for c_item in detected_contradictions:
                finding_obj = await analysis_repo.add_finding(
                    analysis_id=analysis.id,
                    agent_type=AgentType.CONTRADICTION,
                    finding_text=c_item["explanation"],
                    confidence_score=c_item["confidence"],
                    source_references={
                        "classification": c_item["classification"],
                        "contradiction_type": c_item["contradiction_type"],
                        "explanation": c_item["explanation"],
                        "source_a": c_item["source_a"],
                        "source_b": c_item["source_b"],
                    },
                    raw_llm_response=c_item,
                )
                all_contradiction_findings.append(finding_obj)

        # ── Phase 3D: Legal Research Agent ──
        await analysis_repo.delete_legal_research_findings_by_case(case_id)

        # Construct research context
        context_parts = []
        if all_created_entities:
            ent_summary = ", ".join([f"{e.entity_type}: {e.entity_text}" for e in all_created_entities[:15]])
            context_parts.append(f"EXTRACTED ENTITIES: {ent_summary}")

        if all_evidence_findings:
            ev_summary = "; ".join([f"{f.finding_text}" for f in all_evidence_findings[:10]])
            context_parts.append(f"FACTUAL EVIDENCE: {ev_summary}")

        if all_contradiction_findings:
            c_summary = "; ".join([f"{f.finding_text}" for f in all_contradiction_findings[:5]])
            context_parts.append(f"CONTRADICTIONS: {c_summary}")

        research_context = "\n".join(context_parts) if context_parts else "General legal document review."

        research_data = await legal_research_agent.conduct_research(context_text=research_context)

        all_legal_research_findings = []
        for r_item in research_data:
            finding_obj = await analysis_repo.add_finding(
                analysis_id=analysis.id,
                agent_type=AgentType.LEGAL_RESEARCH,
                finding_text=f"{r_item['research_question']} — {r_item['legal_proposition']}",
                confidence_score=r_item["confidence"],
                source_references={
                    "research_question": r_item["research_question"],
                    "authority_type": r_item["authority_type"],
                    "title": r_item["title"],
                    "citation": r_item["citation"],
                    "legal_proposition": r_item["legal_proposition"],
                    "source_name": r_item["source_name"],
                    "source_url": r_item["source_url"],
                    "verification_status": r_item["verification_status"],
                },
                raw_llm_response=r_item,
            )
            all_legal_research_findings.append(finding_obj)

        # Update final status
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = func.now()
        case.status = CaseStatus.COMPLETED
        await db.commit()
        await db.refresh(analysis)

        logger.info(
            f"Analysis {analysis.id} completed. Extracted {len(all_created_entities)} entities, "
            f"{len(all_evidence_findings)} evidence findings, {len(all_contradiction_findings)} contradictions, "
            f"and {len(all_legal_research_findings)} legal research findings."
        )

        return {
            "analysis": analysis,
            "entities": all_created_entities,
            "evidence_findings": all_evidence_findings,
            "contradiction_findings": all_contradiction_findings,
            "legal_research_findings": all_legal_research_findings,
            "message": (
                f"Successfully completed analysis: {len(all_created_entities)} entities, "
                f"{len(all_evidence_findings)} evidence findings, {len(all_contradiction_findings)} contradictions, "
                f"{len(all_legal_research_findings)} legal research findings."
            ),
        }


# Singleton instance
analysis_service = AnalysisService()
