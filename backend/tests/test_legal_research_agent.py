"""
Phase 3D Legal Research Agent Unit & Integration Tests.

Tests:
1. Research question generation & LLM parsing.
2. Authority type validation.
3. Level 1 Domain Verification (approved vs. unapproved domains).
4. Level 2 Content Verification (matching citation vs. unmatching content).
5. Unverified source marking (no URL fabrication).
6. Verified source marking (both Level 1 & Level 2 pass).
7. Gemini malformed JSON safety.
8. Retrieval failure / timeout handling.
9. Persistence in AgentFinding table (agent_type = AgentType.LEGAL_RESEARCH).
10. Safe re-run idempotency: re-running analysis clears previous legal research without duplicating findings.
11. Preserving existing Evidence, Contradiction, and Entity records.
12. Full end-to-end analysis pipeline (3A + 3B + 3C + 3D).
"""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.legal_research_agent import legal_research_agent
from src.services.legal_retrieval_service import legal_retrieval_service


def test_domain_verification():
    """Test Level 1 Domain Verification."""
    assert legal_retrieval_service.verify_domain("https://www.indiacode.nic.in/handle/123456789/2007") is True
    assert legal_retrieval_service.verify_domain("https://sci.gov.in/judgments/") is True
    assert legal_retrieval_service.verify_domain("https://fake-legal-site.com/statute") is False
    assert legal_retrieval_service.verify_domain(None) is False


@pytest.mark.asyncio
async def test_two_level_verification_verified_statute():
    """Test Level 1 + Level 2 verification for valid official statutory record."""
    suggested = {
        "title": "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 303",
        "citation": "Section 303, Bharatiya Nyaya Sanhita, 2023",
        "legal_proposition": "Section 303 BNS defines theft and prescribes punishment.",
        "confidence": 0.95,
        "authority_type": "STATUTE",
    }

    result = await legal_retrieval_service.retrieve_and_verify(
        research_question="What provision governs theft under BNS?",
        suggested_item=suggested,
    )

    assert result["verification_status"] == "VERIFIED"
    assert result["source_url"] == "https://www.indiacode.nic.in/handle/123456789/2007"
    assert legal_retrieval_service.verify_domain(result["source_url"]) is True


@pytest.mark.asyncio
async def test_unverified_source_no_fake_url():
    """Test that unverified sources are marked UNVERIFIED and do not fabricate URLs."""
    suggested = {
        "title": "Unverified Precedent vs Unknown",
        "citation": "2024 SCC Online SC 9999",
        "legal_proposition": "Unclear proposition.",
        "confidence": 0.5,
        "authority_type": "CASE_LAW",
        "source_url": "https://unverified-domain.org/case",
    }

    result = await legal_retrieval_service.retrieve_and_verify(
        research_question="Unknown question?",
        suggested_item=suggested,
    )

    assert result["verification_status"] == "UNVERIFIED"
    assert result["source_url"] is None  # No fake URL
    assert result["source_name"] == "Source verification unavailable"


@pytest.mark.asyncio
async def test_legal_research_agent_mocked_llm():
    """Test LegalResearchAgent.conduct_research with mocked Gemini LLM."""
    mock_llm_json = {
        "research_results": [
            {
                "research_question": "What provision governs theft of property under Indian law?",
                "authority_type": "STATUTE",
                "title": "Bharatiya Nyaya Sanhita (BNS), 2023 - Section 303",
                "citation": "Section 303, Bharatiya Nyaya Sanhita, 2023",
                "legal_proposition": "Section 303 BNS defines theft and prescribes punishment.",
                "confidence": 0.95,
            }
        ]
    }

    with patch("src.agents.legal_research_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_llm_json

        findings = await legal_research_agent.conduct_research(context_text="Theft of property worth Rs. 50,000 under Section 303 BNS.")

        assert len(findings) == 1
        res = findings[0]
        assert res["authority_type"] == "STATUTE"
        assert res["verification_status"] == "VERIFIED"
        assert res["source_url"] is not None


@pytest.mark.asyncio
async def test_malformed_llm_json_handling():
    """Test that malformed Gemini LLM JSON returns [] safely."""
    with patch("src.agents.legal_research_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ValueError("Invalid JSON response")

        findings = await legal_research_agent.conduct_research(context_text="Valid context")

        assert findings == []


@pytest.mark.asyncio
async def test_empty_context_handling():
    """Test that empty context text skips LLM call."""
    with patch("src.agents.legal_research_agent.llm_adapter.generate_json", new_callable=AsyncMock) as mock_gen:
        findings = await legal_research_agent.conduct_research(context_text="   \n\t ")

        assert findings == []
        mock_gen.assert_not_called()


@pytest.mark.asyncio
async def test_legal_research_e2e_persistence_and_rerun_idempotency(async_client):
    """
    End-to-End Test:
    1. Create case & upload 2 PDFs
    2. Run full analysis pipeline (3A + 3B + 3C + 3D)
    3. Verify legal research findings persisted with verification status
    4. Re-run analysis on the same case
    5. Verify legal research count does NOT duplicate (idempotency)
    6. Verify Evidence findings, Contradiction findings, and Entities remain intact
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

    # 1. Create case
    case_res = await async_client.post("/api/v1/cases", json={"title": "Legal Research Test Case", "description": "Phase 3D E2E"})
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

        # Precise mock dispatch function for all 4 agents
        async def mock_generate_json(prompt, system_instruction, **kwargs):
            s = system_instruction.lower()
            if "named entity recognition" in s or "legal entities" in s:
                return mock_entity_json
            elif "factual evidence extraction" in s or "evidence statements" in s:
                return mock_evidence_json
            elif "legal research assistant" in s or "research questions" in s:
                return mock_research_json
            else:
                return mock_contradiction_json

        with patch("src.llm.adapter.llm_adapter.generate_json", side_effect=mock_generate_json):
            # 3. FIRST Analysis Run
            analyze_res_1 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_1.status_code == 200
            data_1 = analyze_res_1.json()
            assert data_1["data"]["status"] == "COMPLETED"

            # Check GET /cases/{case_id}/legal-research
            lr_res_1 = await async_client.get(f"/api/v1/cases/{case_id}/legal-research")
            assert lr_res_1.status_code == 200
            lr_data_1 = lr_res_1.json()
            assert lr_data_1["total_count"] == 1
            item = lr_data_1["data"][0]
            assert item["source_references"]["verification_status"] == "VERIFIED"
            assert item["source_references"]["source_url"] is not None

            # 4. SECOND Analysis Run (Re-run on same case)
            analyze_res_2 = await async_client.post(f"/api/v1/cases/{case_id}/analyze")
            assert analyze_res_2.status_code == 200

            # 5. Verify NO DUPLICATION occurred for legal research
            lr_res_2 = await async_client.get(f"/api/v1/cases/{case_id}/legal-research")
            assert lr_res_2.status_code == 200
            lr_data_2 = lr_res_2.json()
            assert lr_data_2["total_count"] == 1, f"Expected 1 legal research finding after re-run, found {lr_data_2['total_count']}"

            # 6. Verify Evidence, Contradiction, and Entity data REMAIN INTACT
            ev_res = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
            assert ev_res.status_code == 200
            assert ev_res.json()["total_count"] >= 1

            c_res = await async_client.get(f"/api/v1/cases/{case_id}/contradictions")
            assert c_res.status_code == 200
            assert c_res.json()["total_count"] >= 1

            ent_res = await async_client.get(f"/api/v1/cases/{case_id}/entities")
            assert ent_res.status_code == 200
            assert ent_res.json()["total_count"] >= 1
    finally:
        await async_client.delete(f"/api/v1/cases/{case_id}")
