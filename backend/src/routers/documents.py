"""
Documents Router — Upload, list, preview, and manage case documents.

Implements Phase 2:
- PDF upload validation (type, magic bytes, file size)
- Secure file storage
- Page-by-page text extraction via pdfplumber
- NLP text cleaning pipeline
- Error handling without exposing Python stack traces
"""

import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.exceptions import (
    CaseNotFoundError,
    DocumentNotFoundError,
    FileTooLargeError,
)
from src.models.case import Case, CaseStatus
from src.models.document import Document, DocumentType, ExtractionStatus
from src.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
)
from src.services.document_service import document_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/cases/{case_id}/documents", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: UUID,
    file: UploadFile = File(...),
    document_type: str = Form(default="OTHER"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF document to a case and perform text extraction & cleaning.

    Validates:
    - Case exists
    - File extension is .pdf
    - File magic bytes match %PDF-
    - File size does not exceed MAX_FILE_SIZE_MB
    """
    # 1. Validate case exists
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    # 2. Sanitize original filename (prevent path traversal)
    original_filename = Path(file.filename or "document.pdf").name
    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "Only PDF files (.pdf) are supported."},
        )

    # 3. Read content and validate size + magic bytes
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_FILE", "message": "The uploaded PDF file is empty (0 bytes)."},
        )

    if len(content) > settings.max_file_size_bytes:
        raise FileTooLargeError(original_filename, settings.MAX_FILE_SIZE_MB)

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PDF_FORMAT", "message": "File header does not match a valid PDF format."},
        )

    # 4. Parse document type enum
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        doc_type = DocumentType.OTHER

    # 5. Secure file storage path
    file_id = uuid4()
    case_upload_dir = settings.upload_path / str(case_id)
    case_upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = case_upload_dir / f"{file_id}.pdf"

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as storage_err:
        logger.error(f"Failed to write file to disk '{file_path}': {storage_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "STORAGE_ERROR", "message": "Failed to store uploaded file on server."},
        )

    # 6. Create initial document database record (status: EXTRACTING)
    document = Document(
        id=file_id,
        case_id=case_id,
        filename=original_filename,
        document_type=doc_type,
        file_path=str(file_path),
        extraction_status=ExtractionStatus.EXTRACTING,
    )
    db.add(document)
    await db.flush()

    # Update case status if this is the first document
    if case.status == CaseStatus.CREATED:
        case.status = CaseStatus.DOCUMENTS_UPLOADED

    # 7. Perform PDF Text Extraction & Cleaning
    try:
        extraction_result = await document_service.extract_text(str(file_path))
        raw_text = extraction_result["text"]
        page_count = extraction_result["page_count"]
        cleaned_text = document_service.clean_text(raw_text)

        document.extracted_text = raw_text
        document.cleaned_text = cleaned_text
        document.page_count = page_count
        document.extraction_status = ExtractionStatus.COMPLETED
        document.extraction_error = None
    except Exception as extract_err:
        logger.error(f"Text extraction failed for document '{file_id}': {extract_err}")
        document.extraction_status = ExtractionStatus.FAILED
        document.extraction_error = f"Extraction failed: {str(extract_err)}"

    await db.commit()
    await db.refresh(document)

    return {
        "status": "success",
        "message": f"Document '{original_filename}' uploaded and processed.",
        "data": {
            "id": str(document.id),
            "filename": document.filename,
            "document_type": document.document_type.value,
            "extraction_status": document.extraction_status.value,
            "page_count": document.page_count,
            "has_extracted_text": bool(document.extracted_text),
            "has_cleaned_text": bool(document.cleaned_text),
        },
    }


@router.get("/cases/{case_id}/documents", response_model=DocumentListResponse)
async def list_documents(case_id: UUID, db: AsyncSession = Depends(get_db)):
    """List all documents for a given case."""
    case = await db.get(Case, case_id)
    if not case:
        raise CaseNotFoundError(str(case_id))

    stmt = (
        select(Document)
        .where(Document.case_id == case_id)
        .order_by(Document.uploaded_at.desc())
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()

    doc_responses = [
        DocumentResponse(
            id=d.id,
            case_id=d.case_id,
            filename=d.filename,
            document_type=d.document_type,
            extraction_status=d.extraction_status,
            page_count=d.page_count,
            uploaded_at=d.uploaded_at,
            has_extracted_text=bool(d.extracted_text and d.extracted_text.strip()),
            has_cleaned_text=bool(d.cleaned_text and d.cleaned_text.strip()),
        )
        for d in docs
    ]

    return DocumentListResponse(data=doc_responses, count=len(doc_responses))


@router.get("/documents/{doc_id}")
async def get_document(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get document details including extracted text and cleaned text."""
    document = await db.get(Document, doc_id)
    if not document:
        raise DocumentNotFoundError(str(doc_id))

    return {
        "status": "success",
        "data": DocumentDetailResponse(
            id=document.id,
            case_id=document.case_id,
            filename=document.filename,
            document_type=document.document_type,
            extraction_status=document.extraction_status,
            extraction_error=document.extraction_error,
            extracted_text=document.extracted_text,
            cleaned_text=document.cleaned_text,
            page_count=document.page_count,
            uploaded_at=document.uploaded_at,
        ).model_dump(),
    }


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a document record and its underlying PDF file from disk."""
    document = await db.get(Document, doc_id)
    if not document:
        raise DocumentNotFoundError(str(doc_id))

    # Delete file from filesystem safely
    file_path = Path(document.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as file_err:
            logger.warning(f"Failed to remove physical file '{file_path}': {file_err}")

    await db.delete(document)
    await db.commit()
