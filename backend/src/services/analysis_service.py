"""
Analysis Service — Orchestrates Phase 3A Entity Extraction and Phase 3B Evidence Extraction.

Implements:
- Phase 3A: Legal Entity Extraction via NLPService / Gemini LLM
- Phase 3B: Factual Evidence Extraction via EvidenceAgent / Gemini LLM
- Idempotent re-run behavior (clears previous entities and evidence findings for case)
- Traceability back to source documents
- Analysis status lifecycle updates
"""

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.evidence_agent import evidence_agent
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
    """Orchestrates Phase 3A & Phase 3B analysis pipeline."""

    async def run_analysis(self, case_id: UUID, db: AsyncSession) -> dict:
        """
        Execute full Phase 3A & Phase 3B analysis for a case.

        Args:
            case_id: UUID of the Case.
            db: AsyncSession database session.

        Returns:
            dict containing:
                - analysis: Analysis model instance
                - entities: List of ExtractedEntity instances
                - findings: List of AgentFinding instances (evidence)
                - entity_groups: Dict of entities grouped by entity_type
                - evidence_groups: Dict of evidence findings grouped by category
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
                "findings": [],
                "entity_groups": {},
                "evidence_groups": {},
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

        all_created_findings = []
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
                all_created_findings.append(finding_obj)

        # Update final status
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = func.now()
        case.status = CaseStatus.COMPLETED
        await db.commit()
        await db.refresh(analysis)

        # Group entities
        entity_groups = {}
        for ent in all_created_entities:
            grp = entity_groups.setdefault(ent.entity_type, [])
            grp.append(ent)

        # Group evidence findings
        evidence_groups = {}
        for f in all_created_findings:
            cat = (f.source_references or {}).get("category", "FACT")
            grp = evidence_groups.setdefault(cat, [])
            grp.append(f)

        logger.info(
            f"Analysis {analysis.id} completed. Extracted {len(all_created_entities)} entities and "
            f"{len(all_created_findings)} evidence findings across {len(valid_docs)} documents."
        )

        return {
            "analysis": analysis,
            "entities": all_created_entities,
            "findings": all_created_findings,
            "entity_groups": entity_groups,
            "evidence_groups": evidence_groups,
            "message": f"Successfully extracted {len(all_created_entities)} entities and {len(all_created_findings)} evidence findings.",
        }


# Singleton instance
analysis_service = AnalysisService()
