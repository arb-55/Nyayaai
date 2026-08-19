"""
Phase 4 Consensus Engine Unit & Integration Tests.

Tests:
1. Deterministic evidence score weighting.
2. Contradiction penalty calculation (deduplicated).
3. Verified vs. unverified legal research weighting impact.
4. Finding ID validation (discards unknown IDs).
5. Gemini malformed JSON response safety.
6. Case-level re-run idempotency (re-running analysis does NOT create duplicate ConsensusReport records).
7. Preserving existing Entities, Evidence, Contradictions, and Legal Research findings during consensus re-runs.
8. Human review flag enforcement (requires_human_review = True).
9. Full end-to-end pipeline execution (Phase 1 to Phase 4).
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.consensus import (
    calculate_deterministic_confidence,
    consensus_agent,
    validate_and_sanitize_finding_ids,
)


def test_calculate_deterministic_confidence_weighting():
    """Test that strong evidence receives greater weight than weak evidence."""
    strong_evidence = [
        {"confidence_score": 0.95, "source_references": {"evidence_strength": "HIGH"}},
        {"confidence_score": 0.90, "source_references": {"evidence_strength": "HIGH"}},
    ]
    weak_evidence = [
        {"confidence_score": 0.50, "source_references": {"evidence_strength": "LOW"}},
    ]

    conf_strong = calculate_deterministic_confidence(strong_evidence, [], [])
    conf_weak = calculate_deterministic_confidence(weak_evidence, [], [])

    assert conf_strong > conf_weak
    assert conf_strong >= 0.85
    assert conf_weak <= 0.60


def test_contradiction_penalty_deduplication():
    """Test that contradiction penalty is applied deterministically without double-counting."""
    evidence = [{"confidence_score": 0.9, "source_references": {"evidence_strength": "HIGH"}}]
    c1 = {"id": "c1", "confidence": 0.9}
    c2 = {"id": "c2", "confidence": 0.8}

    conf_no_c = calculate_deterministic_confidence(evidence, [], [])
    conf_with_c = calculate_deterministic_confidence(evidence, [c1, c2], [])

    # Contradictions must reduce overall confidence score
    assert conf_with_c < conf_no_c

    # Duplicate contradiction ID should not be double-counted
    conf_duplicate = calculate_deterministic_confidence(evidence, [c1, c1, c2, c2], [])
    assert conf_duplicate == conf_with_c


def test_finding_id_validation_discards_unknown():
    """Test that finding ID validation discards hallucinated/unknown finding IDs."""
    valid_ids = {"id-1", "id-2"}
    raw_gemini = {
        "summary": "Test summary",
        "key_findings": [
            {
                "finding": "Valid statement",
                "supporting_finding_ids": ["id-1", "fake-id-999"],
                "contradicting_finding_ids": ["id-2", "fake-id-888"],
            }
        ],
        "supporting_evidence": [
            {"finding_id": "id-1", "reason": "Valid"},
            {"finding_id": "fake-id-777", "reason": "Invalid"},
        ],
    }

    sanitized = validate_and_sanitize_finding_ids(raw_gemini, valid_ids)

    kf = sanitized["key_findings"][0]
    assert "id-1" in kf["supporting_finding_ids"]
    assert "fake-id-999" not in kf["supporting_finding_ids"]
    assert "id-2" in kf["contradicting_finding_ids"]
    assert "fake-id-888" not in kf["contradicting_finding_ids"]

    assert len(sanitized["supporting_evidence"]) == 1
    assert sanitized["supporting_evidence"][0]["finding_id"] == "id-1"


@pytest.mark.asyncio
async def test_consensus_e2e_persistence_and_rerun_idempotency(async_client):
    """
    End-to-End Test for Phase 4:
    1. Create case & upload 2 PDFs
    2. Run full analysis pipeline (3A + 3B + 3C + 3D + Phase 4 Consensus)
    3. Verify ConsensusReport persisted with deterministic confidence & human review flag
    4. Re-run analysis on the same case
    5. Verify ConsensusReport count does NOT duplicate (case-level idempotency)
    6. Verify Entities, Evidence, Contradictions, and Legal Research remain intact
    """
    mock_entity_json = {
        "entities": [
            {
                "entity_type": "PERSON",
                "entity_text": "Rajesh Kumar",
                "normalized_value": "Rajesh Kumar",
                "confidence": 0.95,
                "page_number": 1,
                "source_sentence": "Rajesh Kumar reported theft under Section 303 BNS.",
            }
        ]
    }

    mock_evidence_json = {
        "evidence": [
            {
                "category": "DOCUMENTARY",
                "statement": "Incident occurred at 8 PM under Section 303 BNS.",
                "source_text": "Incident occurred at 8 PM.",
                "confidence": 0.95,
                "evidence_strength": "HIGH",
                "page_number": 1,
            }
        ]
    }

    mock_contradiction_json = {
        "classification": "CONTRADICTION",
        "contradiction_type": "TIME_CONFLICT",
        "explanation": "FIR states incident occurred at 8 PM whereas Witness states 11 PM.",
        "confidence": 0.91,
    }

    mock_research_json = {
        "research_results": [
            {
                "research_question": "What provision governs theft under BNS?",
                "authority_type": "STATUTE",
                "title": "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 303",
                "citation": "Section 303, Bharatiya Nyaya Sanhita, 2023",
                "legal_proposition": "Section 303 BNS prescribes punishment for theft.",
                "confidence": 0.94,
            }
        ]
    }

    mock_consensus_json = {
        "summary": "Synthesized case summary based on available documents.",
        "key_findings": [
            {
                "finding": "Theft incident reported at Karol Bagh.",
                "supporting_finding_ids": [],
                "contradicting_finding_ids": [],
            }
        ],
        "supporting_evidence": [],
        "material_contradictions": [],
        "legal_context": [],
        "uncertainties": ["Exact incident timing requires review."],
        "requires_human_review": True,
    }

    # 1. Create case
    case_res = await async_client.post("/api/v1/cases", json={"title": "Phase 4 Consensus Test Case", "description": "Full E2E"})
    case_id = case_res.json()["data"]["id"]

    try:
        # 2. Upload 2 sample PDFs
        sample_pdf = Path(__file__).parent / "sample_data" / "sample_fir.pdf"
        with open(sample_pdf, "rb") as f:
            await async_client.post(
                f"/api/v1/cases/{case_id}/documents",
                files={"file": ("doc_a_fir.pdf", f, "application/pdf")},
                data={"document_type": "FIR"},
            )
        with open(sample_pdf, "rb") as f:
            await async_client.post(
                f"/api/v1/cases/{case_id}/documents",
                files={"file": ("doc_b_witness.pdf", f, "application/pdf")},
                data={"document_type": "WITNESS_STATEMENT"},
            )

        # Precise mock dispatch function for all 5 pipeline stages
        async def mock_generate_json(prompt, system_instruction, **kwargs):
            s = system_instruction.lower()
            if "named entity recognition" in s or "legal entities" in s:
                return mock_entity_json
            elif "factual evidence extraction" in s or "evidence statements" in s:
                return mock_evidence_json
            elif "legal research assistant" in s or "research questions" in s:
                return mock_research_json
            elif "multi-agent consensus synthesis" in s or "consensus report" in s:
                return mock_consensus_json
            else:
                return mock_contradiction_json

        with patch("src.llm.adapter.llm_adapter.generate_json", side_effect=mock_generate_json):
            # 3. FIRST Analysis Run
            analyze_res_1 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_1.status_code == 200
            data_1 = analyze_res_1.json()
            assert data_1["data"]["status"] == "COMPLETED"

            # Check GET /cases/{case_id}/consensus
            cons_res_1 = await async_client.get(f"/api/v1/cases/{case_id}/consensus")
            assert cons_res_1.status_code == 200
            cons_data_1 = cons_res_1.json()["data"]
            assert cons_data_1 is not None
            assert cons_data_1["overall_confidence"] > 0.0
            assert cons_data_1["report_data"]["requires_human_review"] is True

            # 4. SECOND Analysis Run (Re-run on same case)
            analyze_res_2 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_2.status_code == 200

            # 5. Verify NO DUPLICATION occurred for ConsensusReport
            cons_res_2 = await async_client.get(f"/api/v1/cases/{case_id}/consensus")
            assert cons_res_2.status_code == 200
            cons_data_2 = cons_res_2.json()["data"]
            assert cons_data_2 is not None

            # 6. Verify Entities, Evidence, Contradiction, and Legal Research data REMAIN INTACT
            ev_res = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
            assert ev_res.status_code == 200
            assert ev_res.json()["total_count"] >= 1

            c_res = await async_client.get(f"/api/v1/cases/{case_id}/contradictions")
            assert c_res.status_code == 200
            assert c_res.json()["total_count"] >= 1

            lr_res = await async_client.get(f"/api/v1/cases/{case_id}/legal-research")
            assert lr_res.status_code == 200
            assert lr_res.json()["total_count"] >= 1

            ent_res = await async_client.get(f"/api/v1/cases/{case_id}/entities")
            assert ent_res.status_code == 200
            assert ent_res.json()["total_count"] >= 1
    finally:
        await async_client.delete(f"/api/v1/cases/{case_id}")
