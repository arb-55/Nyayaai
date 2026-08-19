"""
Consensus Engine — Synthesizes multi-agent outputs into a structured, human-reviewable consensus report.

Implements Phase 4:
- Deterministic score weighting layer (Gemini does NOT calculate overall_confidence)
- Deduplicated contradiction penalty calculation (prevents double-counting)
- Strict finding ID validation (discards unknown/hallucinated IDs)
- Factual evidence vs. legal context separation
- Human-review requirement enforcement
"""

import logging
from typing import Any

from src.agents.prompts.consensus import (
    CONSENSUS_SYSTEM_INSTRUCTION,
    build_consensus_prompt,
)
from src.llm.adapter import llm_adapter

logger = logging.getLogger(__name__)

STRENGTH_WEIGHTS = {
    "HIGH": 1.0,
    "MEDIUM": 0.7,
    "LOW": 0.4,
}


def calculate_deterministic_confidence(
    evidence_findings: list[dict],
    contradiction_findings: list[dict],
    legal_research_findings: list[dict],
) -> float:
    """
    Calculate deterministic overall analysis confidence score.

    Gemini is NOT trusted to calculate overall_confidence.

    Formula:
    1. Base Evidence Score (S_ev): Weighted average of evidence findings based on strength & confidence.
    2. Contradiction Penalty (P_con): Overall adjustment applying a 0.10 penalty per unique material contradiction (capped at 0.40 max).
    3. Legal Verification Bonus (B_legal): +0.05 bonus if verified legal authorities exist.

    Final Score = clamp(S_ev - P_con + B_legal, 0.10, 0.95)
    """
    if not evidence_findings and not contradiction_findings and not legal_research_findings:
        return 0.0

    # 1. Base Evidence Score
    if evidence_findings:
        total_weight = 0.0
        weighted_sum = 0.0
        for f in evidence_findings:
            refs = f.get("source_references") or {}
            strength = str(refs.get("evidence_strength", "HIGH")).upper()
            w = STRENGTH_WEIGHTS.get(strength, 1.0)
            conf = float(f.get("confidence_score") or f.get("confidence") or 0.9)
            weighted_sum += w * conf
            total_weight += w

        s_evidence = (weighted_sum / total_weight) if total_weight > 0 else 0.7
    else:
        s_evidence = 0.5

    # 2. Contradiction Penalty (Deduplicated unique contradictions)
    unique_contradiction_ids = set()
    total_penalty = 0.0
    for c in contradiction_findings:
        cid = str(c.get("id") or c.get("finding_id") or hash(str(c)))
        if cid in unique_contradiction_ids:
            continue
        unique_contradiction_ids.add(cid)

        conf = float(c.get("confidence_score") or c.get("confidence") or 0.8)
        # Apply 0.10 penalty per unique material contradiction
        total_penalty += 0.10 * conf

    p_contradiction = min(0.40, total_penalty)

    # 3. Legal Research Verification Bonus
    has_verified_legal = any(
        (f.get("source_references") or {}).get("verification_status") == "VERIFIED"
        for f in legal_research_findings
    )
    b_legal = 0.05 if has_verified_legal else 0.0

    # Final Score Calculation
    final_conf = s_evidence - p_contradiction + b_legal
    clamped_conf = round(max(0.10, min(0.95, final_conf)), 2)

    logger.info(
        f"Deterministic Confidence Calculation: S_ev={s_evidence:.2f}, "
        f"P_con={p_contradiction:.2f}, B_legal={b_legal:.2f} => Final={clamped_conf}"
    )
    return clamped_conf


def validate_and_sanitize_finding_ids(raw_json: dict, valid_finding_ids: set[str]) -> dict:
    """
    Validate all finding IDs referenced by Gemini. Discard any unknown/hallucinated IDs.
    """
    sanitized = dict(raw_json)

    # 1. Key Findings
    key_findings = sanitized.get("key_findings", [])
    if isinstance(key_findings, list):
        clean_keys = []
        for k in key_findings:
            if not isinstance(k, dict):
                continue
            sup = [fid for fid in k.get("supporting_finding_ids", []) if str(fid) in valid_finding_ids]
            con = [fid for fid in k.get("contradicting_finding_ids", []) if str(fid) in valid_finding_ids]
            clean_keys.append({
                "finding": str(k.get("finding", "")).strip(),
                "supporting_finding_ids": sup,
                "contradicting_finding_ids": con,
            })
        sanitized["key_findings"] = clean_keys

    # 2. Supporting Evidence
    sup_ev = sanitized.get("supporting_evidence", [])
    if isinstance(sup_ev, list):
        sanitized["supporting_evidence"] = [
            {"finding_id": str(item["finding_id"]), "reason": str(item.get("reason", ""))}
            for item in sup_ev
            if isinstance(item, dict) and str(item.get("finding_id")) in valid_finding_ids
        ]

    # 3. Material Contradictions
    mat_con = sanitized.get("material_contradictions", [])
    if isinstance(mat_con, list):
        sanitized["material_contradictions"] = [
            {"finding_id": str(item["finding_id"]), "impact": str(item.get("impact", ""))}
            for item in mat_con
            if isinstance(item, dict) and str(item.get("finding_id")) in valid_finding_ids
        ]

    # 4. Legal Context
    leg_ctx = sanitized.get("legal_context", [])
    if isinstance(leg_ctx, list):
        sanitized["legal_context"] = [
            {"finding_id": str(item["finding_id"]), "relevance": str(item.get("relevance", ""))}
            for item in leg_ctx
            if isinstance(item, dict) and str(item.get("finding_id")) in valid_finding_ids
        ]

    return sanitized


class ConsensusAgent:
    """Agent responsible for multi-agent consensus synthesis."""

    async def synthesize_consensus(
        self,
        case_id: str,
        entities: list[dict],
        evidence_findings: list[dict],
        contradiction_findings: list[dict],
        legal_research_findings: list[dict],
    ) -> dict:
        """
        Synthesize multi-agent outputs into a structured ConsensusReport.

        Args:
            case_id: Case UUID string.
            entities: Extracted entities list.
            evidence_findings: Evidence findings list.
            contradiction_findings: Contradiction findings list.
            legal_research_findings: Legal research findings list.

        Returns:
            Dict matching ConsensusReport report_data schema with deterministic overall_confidence.
        """
        # 1. Collect all valid finding IDs
        valid_finding_ids = set()
        for e in entities:
            if e.get("id"):
                valid_finding_ids.add(str(e["id"]))
        for f in evidence_findings:
            if f.get("id"):
                valid_finding_ids.add(str(f["id"]))
        for c in contradiction_findings:
            if c.get("id"):
                valid_finding_ids.add(str(c["id"]))
        for r in legal_research_findings:
            if r.get("id"):
                valid_finding_ids.add(str(r["id"]))

        # 2. Calculate deterministic confidence
        deterministic_conf = calculate_deterministic_confidence(
            evidence_findings=evidence_findings,
            contradiction_findings=contradiction_findings,
            legal_research_findings=legal_research_findings,
        )

        # 3. Construct context for Gemini synthesis
        context_parts = []
        if entities:
            ent_str = "; ".join([f"ID[{e.get('id')}]: {e.get('entity_type')}={e.get('entity_text')}" for e in entities[:15]])
            context_parts.append(f"ENTITIES: {ent_str}")

        if evidence_findings:
            ev_str = "; ".join([f"ID[{f.get('id')}]: {f.get('finding_text')}" for f in evidence_findings[:15]])
            context_parts.append(f"EVIDENCE FINDINGS: {ev_str}")

        if contradiction_findings:
            c_str = "; ".join([f"ID[{c.get('id')}]: {c.get('finding_text')}" for c in contradiction_findings[:10]])
            context_parts.append(f"CONTRADICTIONS: {c_str}")

        if legal_research_findings:
            r_str = "; ".join([
                f"ID[{r.get('id')}]: {(r.get('source_references') or {}).get('citation')} - Status: {(r.get('source_references') or {}).get('verification_status')}"
                for r in legal_research_findings[:10]
            ])
            context_parts.append(f"LEGAL RESEARCH: {r_str}")

        context_text = "\n".join(context_parts) if context_parts else "No findings recorded for case."

        prompt = build_consensus_prompt(context_text=context_text)

        # 4. Call Gemini LLM for qualitative synthesis
        try:
            raw_result = await llm_adapter.generate_json(
                prompt=prompt,
                system_instruction=CONSENSUS_SYSTEM_INSTRUCTION,
                temperature=0.1,
            )
        except Exception as err:
            logger.error(f"Consensus synthesis LLM call failed for case {case_id}: {err}")
            raw_result = {}

        if not isinstance(raw_result, dict):
            raw_result = {}

        # 5. Sanitize and validate finding IDs
        report_data = validate_and_sanitize_finding_ids(raw_result, valid_finding_ids)

        # 6. Ensure required fallback fields
        summary = str(report_data.get("summary", "")).strip()
        if not summary:
            summary = f"Synthesized analysis report for case containing {len(evidence_findings)} evidence findings and {len(contradiction_findings)} contradictions."

        report_data["summary"] = summary
        report_data["overall_confidence"] = deterministic_conf  # OVERWRITE Gemini confidence
        report_data["requires_human_review"] = True  # Always enforce human review flag

        if "key_findings" not in report_data:
            report_data["key_findings"] = []
        if "supporting_evidence" not in report_data:
            report_data["supporting_evidence"] = []
        if "material_contradictions" not in report_data:
            report_data["material_contradictions"] = []
        if "legal_context" not in report_data:
            report_data["legal_context"] = []
        if "uncertainties" not in report_data:
            report_data["uncertainties"] = []

        logger.info(f"Consensus synthesis completed for case {case_id} with overall confidence {deterministic_conf}.")
        return report_data


# Singleton instance
consensus_agent = ConsensusAgent()
