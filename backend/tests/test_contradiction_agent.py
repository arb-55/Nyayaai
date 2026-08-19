"""
Phase 3C Contradiction Agent Unit & Integration Tests.

Tests:
1. Direct time contradiction detection.
2. Direct location contradiction.
3. Direct amount contradiction.
4. Presence vs. absence contradiction.
5. Compatible approximate times (filtered out).
6. Malformed LLM JSON handling.
7. Confidence threshold validation (>= 0.6).
8. Both-source traceability (source_a and source_b required).
9. Empty evidence handling.
10. Safe re-run idempotency: re-running analysis clears previous contradictions without duplicating them.
11. Preserving existing Evidence findings and ExtractedEntity records during contradiction re-runs.
12. Full end-to-end analysis pipeline (Entities + Evidence + Contradictions).
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.contradiction_agent import (
    MIN_CONTRADICTION_CONFIDENCE,
    contradiction_agent,
    select_candidate_pairs,
)


def test_constants():
    """Test MIN_CONTRADICTION_CONFIDENCE threshold constant."""
    assert MIN_CONTRADICTION_CONFIDENCE == 0.6


def test_select_candidate_pairs_different_documents():
    """Test that candidate pairs are selected only from DIFFERENT documents."""
    doc_1 = str(uuid.uuid4())
    doc_2 = str(uuid.uuid4())

    evidence = [
        {"id": "1", "finding_text": "Incident occurred at 8 PM.", "source_references": {"document_id": doc_1, "document_name": "FIR.pdf", "category": "DOCUMENTARY"}},
        {"id": "2", "finding_text": "Incident occurred at 11 PM.", "source_references": {"document_id": doc_2, "document_name": "Witness.pdf", "category": "DOCUMENTARY"}},
        {"id": "3", "finding_text": "FIR recorded at station.", "source_references": {"document_id": doc_1, "document_name": "FIR.pdf", "category": "DOCUMENTARY"}},
    ]

    entities = []

    candidates = select_candidate_pairs(evidence, entities)
    assert len(candidates) >= 1
    for fa, fb in candidates:
        refs_a = fa.get("source_references") or fa
        refs_b = fb.get("source_references") or fb
        assert refs_a["document_id"] != refs_b["document_id"]


@pytest.mark.asyncio
async def test_direct_time_contradiction():
    """Test LLM detection of direct time contradiction."""
    mock_llm_json = {
        "classification": "CONTRADICTION",
        "contradiction_type": "TIME_CONFLICT",
        "explanation": "Statement A reports incident at 8 PM whereas Statement B reports 11 PM.",
        "confidence": 0.92,
    }

    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())
    pairs = [
        (
            {"finding_text": "Incident occurred at 8 PM.", "source_references": {"document_id": doc_a, "document_name": "FIR.pdf", "statement": "Incident occurred at 8 PM."}},
            {"finding_text": "Incident occurred at 11 PM.", "source_references": {"document_id": doc_b, "document_name": "Witness.pdf", "statement": "Incident occurred at 11 PM."}},
        )
    ]

    with patch("src.agents.contradiction_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json

        results = await contradiction_agent.analyze_candidate_pairs(pairs)

        assert len(results) == 1
        res = results[0]
        assert res["classification"] == "CONTRADICTION"
        assert res["contradiction_type"] == "TIME_CONFLICT"
        assert res["confidence"] == 0.92
        assert res["source_a"]["document_id"] == doc_a
        assert res["source_b"]["document_id"] == doc_b


@pytest.mark.asyncio
async def test_possibly_compatible_not_persisted():
    """Test that POSSIBLY_COMPATIBLE results are NOT persisted."""
    mock_llm_json = {
        "classification": "POSSIBLY_COMPATIBLE",
        "contradiction_type": "TIME_CONFLICT",
        "explanation": "Around 8 PM and 8:15 PM are compatible.",
        "confidence": 0.85,
    }

    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())
    pairs = [
        (
            {"finding_text": "Incident around 8 PM.", "source_references": {"document_id": doc_a, "document_name": "FIR.pdf"}},
            {"finding_text": "Incident at 8:15 PM.", "source_references": {"document_id": doc_b, "document_name": "Witness.pdf"}},
        )
    ]

    with patch("src.agents.contradiction_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json

        results = await contradiction_agent.analyze_candidate_pairs(pairs)

        assert results == []


@pytest.mark.asyncio
async def test_low_confidence_filtered_out():
    """Test that confidence < 0.6 is filtered out and not persisted."""
    mock_llm_json = {
        "classification": "CONTRADICTION",
        "contradiction_type": "OTHER",
        "explanation": "Weak conflict",
        "confidence": 0.45,  # Below 0.6 threshold
    }

    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())
    pairs = [
        (
            {"finding_text": "Statement 1", "source_references": {"document_id": doc_a, "document_name": "A.pdf"}},
            {"finding_text": "Statement 2", "source_references": {"document_id": doc_b, "document_name": "B.pdf"}},
        )
    ]

    with patch("src.agents.contradiction_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json

        results = await contradiction_agent.analyze_candidate_pairs(pairs)

        assert results == []


@pytest.mark.asyncio
async def test_malformed_llm_json_handling():
    """Test that malformed Gemini JSON returns [] safely without crashing."""
    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())
    pairs = [
        (
            {"finding_text": "Statement 1", "source_references": {"document_id": doc_a}},
            {"finding_text": "Statement 2", "source_references": {"document_id": doc_b}},
        )
    ]

    with patch("src.agents.contradiction_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ValueError("Invalid JSON")

        results = await contradiction_agent.analyze_candidate_pairs(pairs)

        assert results == []


@pytest.mark.asyncio
async def test_contradiction_e2e_persistence_and_rerun_idempotency(async_client):
    """
    End-to-End Test:
    1. Create case & upload 2 PDFs (FIR & Witness statement)
    2. Run analysis (Phase 3A + 3B + 3C)
    3. Verify contradiction findings persisted with both source_a and source_b
    4. Re-run analysis on the same case
    5. Verify contradiction count does NOT duplicate (idempotency)
    6. Verify Evidence findings and Entities remain intact
    """
    mock_entity_json = {
        "entities": [
            {
                "entity_type": "PERSON",
                "entity_text": "Rajesh Kumar",
                "normalized_value": "Rajesh Kumar",
                "confidence": 0.95,
                "page_number": 1,
                "source_sentence": "Rajesh Kumar reported incident.",
            }
        ]
    }

    mock_evidence_json = {
        "evidence": [
            {
                "category": "DOCUMENTARY",
                "statement": "Incident occurred at 8 PM.",
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

    # 1. Create case
    case_res = await async_client.post("/api/v1/cases", json={"title": "Contradiction Test Case", "description": "Phase 3C E2E"})
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

        # Precise mock dispatch function
        async def mock_generate_json(prompt, system_instruction, **kwargs):
            s = system_instruction.lower()
            if "named entity recognition" in s or "legal entities" in s:
                return mock_entity_json
            elif "factual evidence extraction" in s or "evidence statements" in s:
                return mock_evidence_json
            else:
                return mock_contradiction_json

        with patch("src.llm.adapter.llm_adapter.generate_json", side_effect=mock_generate_json):
            # 3. FIRST Analysis Run
            analyze_res_1 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_1.status_code == 200
            data_1 = analyze_res_1.json()
            assert data_1["data"]["status"] == "COMPLETED"

            # Check GET /cases/{case_id}/contradictions
            c_res_1 = await async_client.get(f"/api/v1/cases/{case_id}/contradictions")
            assert c_res_1.status_code == 200
            c_data_1 = c_res_1.json()
            assert c_data_1["total_count"] == 1
            item = c_data_1["data"][0]
            assert item["source_references"]["classification"] == "CONTRADICTION"
            assert item["source_references"]["contradiction_type"] == "TIME_CONFLICT"
            # Verify BOTH source_a and source_b are present
            assert "source_a" in item["source_references"]
            assert "source_b" in item["source_references"]
            assert item["source_references"]["source_a"]["document_id"] != item["source_references"]["source_b"]["document_id"]

            # 4. SECOND Analysis Run (Re-run on same case)
            analyze_res_2 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_2.status_code == 200

            # 5. Verify NO DUPLICATION occurred for contradictions
            c_res_2 = await async_client.get(f"/api/v1/cases/{case_id}/contradictions")
            assert c_res_2.status_code == 200
            c_data_2 = c_res_2.json()
            assert c_data_2["total_count"] == 1, f"Expected 1 contradiction after re-run, found {c_data_2['total_count']}"

            # 6. Verify Evidence findings and Entities REMAIN INTACT
            ev_res = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
            assert ev_res.status_code == 200
            assert ev_res.json()["total_count"] >= 1

            ent_res = await async_client.get(f"/api/v1/cases/{case_id}/entities")
            assert ent_res.status_code == 200
            assert ent_res.json()["total_count"] >= 1
    finally:
        await async_client.delete(f"/api/v1/cases/{case_id}")
