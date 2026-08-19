"""
Phase 3B Evidence Agent Unit & Integration Tests.

Tests:
1. Evidence extraction from sample text (mocking LLM adapter).
2. Controlled category and strength validation.
3. Invalid/malformed LLM JSON response handling.
4. Empty document text handling (skips LLM call).
5. Evidence persistence in AgentFinding database table.
6. Source document traceability (document_id, excerpt, page_number).
7. Safe re-run idempotency: verify re-running analysis does NOT duplicate evidence findings.
8. Evidence retrieval API endpoint GET /cases/{case_id}/evidence.
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.agents.evidence_agent import evidence_agent
from src.main import app

SAMPLE_EVIDENCE_TEXT = """
FIRST INFORMATION REPORT (FIR)
FIR No: 102/2026
Police Station: Central Delhi
Date: 15/01/2026

Complainant Rajesh Kumar reported a theft at Karol Bagh market.
Witness Sunita Devi stated she saw the accused fleeing at 4:30 PM.
Financial transfer of Rs. 50,000 recorded in bank statement.
Offense registered under Section 303 of BNS.
"""


def test_evidence_agent_singleton():
    """Test EvidenceAgent import and singleton instantiation."""
    assert evidence_agent is not None


@pytest.mark.asyncio
async def test_extract_evidence_mocked_llm():
    """Test EvidenceAgent.extract_evidence with mocked LLMAdapter output."""
    mock_llm_json = {
        "evidence": [
            {
                "category": "DOCUMENTARY",
                "statement": "FIR No. 102/2026 was registered at Central Delhi Police Station on 15/01/2026.",
                "source_text": "FIR No: 102/2026 Police Station: Central Delhi Date: 15/01/2026",
                "confidence": 0.96,
                "evidence_strength": "HIGH",
                "page_number": 1,
            },
            {
                "category": "TESTIMONY",
                "statement": "Witness Sunita Devi stated she saw the accused fleeing at 4:30 PM.",
                "source_text": "Witness Sunita Devi stated she saw the accused fleeing at 4:30 PM.",
                "confidence": 0.91,
                "evidence_strength": "HIGH",
                "page_number": 1,
            },
            {
                "category": "FINANCIAL",
                "statement": "Financial transfer of Rs. 50,000 recorded in bank statement.",
                "source_text": "Financial transfer of Rs. 50,000 recorded in bank statement.",
                "confidence": 0.88,
                "evidence_strength": "MEDIUM",
                "page_number": 1,
            },
        ]
    }

    doc_id = str(uuid.uuid4())
    with patch("src.agents.evidence_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json

        findings = await evidence_agent.extract_evidence(
            text=SAMPLE_EVIDENCE_TEXT,
            document_id=doc_id,
            filename="sample_fir.pdf",
        )

        assert len(findings) == 3
        cats = [f["category"] for f in findings]
        assert "DOCUMENTARY" in cats
        assert "TESTIMONY" in cats
        assert "FINANCIAL" in cats
        assert all(f["document_id"] == doc_id for f in findings)
        assert findings[0]["evidence_strength"] == "HIGH"


@pytest.mark.asyncio
async def test_invalid_llm_json_handling():
    """Test that malformed LLM JSON returns [] safely without crashing."""
    doc_id = str(uuid.uuid4())
    with patch("src.agents.evidence_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ValueError("Invalid JSON response")

        findings = await evidence_agent.extract_evidence(
            text=SAMPLE_EVIDENCE_TEXT,
            document_id=doc_id,
            filename="fir.pdf",
        )

        assert findings == []


@pytest.mark.asyncio
async def test_empty_text_handling():
    """Test that empty document text skips LLM call."""
    doc_id = str(uuid.uuid4())
    with patch("src.agents.evidence_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        findings = await evidence_agent.extract_evidence(
            text="   \n\t  ",
            document_id=doc_id,
            filename="empty.pdf",
        )

        assert findings == []
        mock_gen.assert_not_called()


@pytest.mark.asyncio
async def test_evidence_e2e_persistence_and_rerun_idempotency(async_client):
    """
    End-to-End Test:
    1. Create case & upload PDF
    2. Run analysis (Phase 3A + 3B)
    3. Verify evidence findings persisted & source traceability
    4. Re-run analysis on the same case
    5. Verify evidence count does NOT duplicate (safe re-run idempotency)
    """
    mock_entity_json = {
        "entities": [
            {
                "entity_type": "PERSON",
                "entity_text": "Rajesh Kumar",
                "normalized_value": "Rajesh Kumar",
                "confidence": 0.95,
                "page_number": 1,
                "source_sentence": "Complainant Rajesh Kumar reported theft.",
            }
        ]
    }

    mock_evidence_json = {
        "evidence": [
            {
                "category": "DOCUMENTARY",
                "statement": "FIR No 102/2026 recorded at Central Delhi.",
                "source_text": "FIR No: 102/2026 Police Station: Central Delhi",
                "confidence": 0.95,
                "evidence_strength": "HIGH",
                "page_number": 1,
            },
            {
                "category": "TESTIMONY",
                "statement": "Witness Sunita Devi statement recorded.",
                "source_text": "Witness Sunita Devi stated she saw the accused.",
                "confidence": 0.90,
                "evidence_strength": "MEDIUM",
                "page_number": 1,
            },
        ]
    }

    # 1. Create case
    case_res = await async_client.post("/api/v1/cases", json={"title": "Idempotency Test Case", "description": "Phase 3B test"})
    case_id = case_res.json()["data"]["id"]

    try:
        # 2. Upload sample PDF
        sample_pdf = Path(__file__).parent / "sample_data" / "sample_fir.pdf"
        with open(sample_pdf, "rb") as f:
            upload_res = await async_client.post(
                f"/api/v1/cases/{case_id}/documents",
                files={"file": ("sample_fir.pdf", f, "application/pdf")},
                data={"document_type": "FIR"},
            )
        assert upload_res.status_code == 201
        doc_id = upload_res.json()["data"]["id"]

        # Mock LLM calls for entities and evidence
        async def mock_generate_json(prompt, system_instruction, **kwargs):
            if "entity" in system_instruction.lower():
                return mock_entity_json
            return mock_evidence_json

        with patch("src.llm.adapter.llm_adapter.generate_json", side_effect=mock_generate_json):
            # 3. First Analysis Run
            analyze_res_1 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_1.status_code == 200
            data_1 = analyze_res_1.json()
            assert data_1["data"]["status"] == "COMPLETED"
            assert data_1["data"]["findings_count"] == 2

            # Fetch evidence endpoint GET /cases/{case_id}/evidence
            ev_res_1 = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
            assert ev_res_1.status_code == 200
            ev_data_1 = ev_res_1.json()
            assert ev_data_1["total_count"] == 2
            assert "DOCUMENTARY" in ev_data_1["data"]
            assert "TESTIMONY" in ev_data_1["data"]

            # Check source traceability
            doc_item = ev_data_1["data"]["DOCUMENTARY"][0]
            assert doc_item["finding_text"] == "FIR No 102/2026 recorded at Central Delhi."
            assert doc_item["source_references"]["document_id"] == doc_id
            assert doc_item["source_references"]["evidence_strength"] == "HIGH"
            assert doc_item["source_references"]["excerpt"] is not None

            # 4. SECOND Analysis Run (Re-run on same case)
            analyze_res_2 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_2.status_code == 200
            data_2 = analyze_res_2.json()

            # 5. Verify NO DUPLICATION occurred
            ev_res_2 = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
            assert ev_res_2.status_code == 200
            ev_data_2 = ev_res_2.json()

            # Total evidence count MUST STILL BE 2 (not 4)
            assert ev_data_2["total_count"] == 2, f"Expected 2 evidence findings after re-run, found {ev_data_2['total_count']}"
    finally:
        await async_client.delete(f"/api/v1/cases/{case_id}")
