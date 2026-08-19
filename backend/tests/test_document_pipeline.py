"""
Phase 2 Document Pipeline Tests.

Tests:
1. Text cleaning unit test.
2. End-to-end PDF upload, text extraction, listing, detail retrieval, deletion.
3. Invalid file type rejection (.txt).
4. Non-existent case ID handling (404).
5. Empty file rejection (400).
"""

import uuid
from pathlib import Path

import pytest

from src.services.document_service import document_service

SAMPLE_PDF_PATH = Path(__file__).parent / "sample_data" / "sample_fir.pdf"


def test_text_cleaning_pipeline():
    """Test NLP text cleaning normalization."""
    raw_text = "FIRST INFORMATION REPORT  \r\n\r\n\r\n\r\nFIR No: 102/2026\t\x00"
    cleaned = document_service.clean_text(raw_text)

    assert "\r\n" not in cleaned
    assert "\x00" not in cleaned
    assert "\n\n\n" not in cleaned
    assert "FIRST INFORMATION REPORT" in cleaned
    assert "FIR No: 102/2026" in cleaned


@pytest.mark.asyncio
async def test_document_pipeline_e2e(async_client):
    """Test full document pipeline: create case -> upload PDF -> list -> get detail -> delete."""
    # 1. Create a test case
    case_res = await async_client.post("/api/v1/cases", json={"title": "Test Pipeline Case", "description": "Phase 2 test"})
    assert case_res.status_code == 201
    case_id = case_res.json()["data"]["id"]

    try:
        # 2. Upload valid PDF
        assert SAMPLE_PDF_PATH.exists()
        with open(SAMPLE_PDF_PATH, "rb") as f:
            upload_res = await async_client.post(
                f"/api/v1/cases/{case_id}/documents",
                files={"file": ("sample_fir.pdf", f, "application/pdf")},
                data={"document_type": "FIR"},
            )

        assert upload_res.status_code == 201
        upload_data = upload_res.json()
        assert upload_data["status"] == "success"
        doc_id = upload_data["data"]["id"]
        assert upload_data["data"]["document_type"] == "FIR"

        # 3. List documents for case
        list_res = await async_client.get(f"/api/v1/cases/{case_id}/documents")
        assert list_res.status_code == 200
        docs = list_res.json()["data"]
        assert len(docs) >= 1
        assert any(d["id"] == doc_id for d in docs)

        # 4. Get document detail and check extracted text
        detail_res = await async_client.get(f"/api/v1/documents/{doc_id}")
        assert detail_res.status_code == 200
        doc_detail = detail_res.json()["data"]
        assert doc_detail["id"] == doc_id
        assert doc_detail["extraction_status"] == "COMPLETED"
        assert doc_detail["extracted_text"] is not None
        assert doc_detail["cleaned_text"] is not None

        # 5. Delete document
        del_res = await async_client.delete(f"/api/v1/documents/{doc_id}")
        assert del_res.status_code == 204

        # Verify document is deleted
        get_deleted = await async_client.get(f"/api/v1/documents/{doc_id}")
        assert get_deleted.status_code == 404
    finally:
        # Cleanup case
        await async_client.delete(f"/api/v1/cases/{case_id}")


@pytest.mark.asyncio
async def test_upload_invalid_file_type(async_client):
    """Test rejecting non-PDF file upload."""
    case_res = await async_client.post("/api/v1/cases", json={"title": "Test Invalid Type Case"})
    case_id = case_res.json()["data"]["id"]

    try:
        res = await async_client.post(
            f"/api/v1/cases/{case_id}/documents",
            files={"file": ("notes.txt", b"Plain text content", "text/plain")},
            data={"document_type": "OTHER"},
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "INVALID_FILE_TYPE"
    finally:
        await async_client.delete(f"/api/v1/cases/{case_id}")


@pytest.mark.asyncio
async def test_upload_non_existent_case(async_client):
    """Test uploading to a non-existent case ID."""
    fake_case_id = str(uuid.uuid4())
    with open(SAMPLE_PDF_PATH, "rb") as f:
        res = await async_client.post(
            f"/api/v1/cases/{fake_case_id}/documents",
            files={"file": ("sample_fir.pdf", f, "application/pdf")},
            data={"document_type": "FIR"},
        )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "CASE_NOT_FOUND"


@pytest.mark.asyncio
async def test_upload_empty_file(async_client):
    """Test uploading an empty 0-byte file."""
    case_res = await async_client.post("/api/v1/cases", json={"title": "Test Empty File Case"})
    case_id = case_res.json()["data"]["id"]

    try:
        res = await async_client.post(
            f"/api/v1/cases/{case_id}/documents",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            data={"document_type": "OTHER"},
        )
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "EMPTY_FILE"
    finally:
        await async_client.delete(f"/api/v1/cases/{case_id}")
