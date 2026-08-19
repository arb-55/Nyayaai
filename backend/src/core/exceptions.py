"""
NyayaAI Backend — Custom Exceptions

Centralized exception classes used across the application.
FastAPI exception handlers in main.py translate these into HTTP responses.
"""

from fastapi import HTTPException, status


class NyayaAIException(Exception):
    """Base exception for NyayaAI application errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class CaseNotFoundError(NyayaAIException):
    """Raised when a case is not found in the database."""

    def __init__(self, case_id: str):
        super().__init__(
            message=f"Case not found: {case_id}",
            code="CASE_NOT_FOUND",
        )


class DocumentNotFoundError(NyayaAIException):
    """Raised when a document is not found."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            code="DOCUMENT_NOT_FOUND",
        )


class AnalysisNotFoundError(NyayaAIException):
    """Raised when an analysis record is not found."""

    def __init__(self, analysis_id: str):
        super().__init__(
            message=f"Analysis not found: {analysis_id}",
            code="ANALYSIS_NOT_FOUND",
        )


class FileTooLargeError(NyayaAIException):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, filename: str, max_mb: int):
        super().__init__(
            message=f"File '{filename}' exceeds the {max_mb}MB limit",
            code="FILE_TOO_LARGE",
        )


class PDFExtractionError(NyayaAIException):
    """Raised when text extraction from a PDF fails."""

    def __init__(self, filename: str, reason: str = ""):
        detail = f" — {reason}" if reason else ""
        super().__init__(
            message=f"Failed to extract text from '{filename}'{detail}",
            code="PDF_EXTRACTION_FAILED",
        )


class AnalysisAlreadyRunningError(NyayaAIException):
    """Raised when analysis is triggered on a case that is already being analyzed."""

    def __init__(self, case_id: str):
        super().__init__(
            message=f"Analysis is already running for case: {case_id}",
            code="ANALYSIS_ALREADY_RUNNING",
        )


class LLMError(NyayaAIException):
    """Raised when a call to the LLM (Gemini) fails."""

    def __init__(self, reason: str = ""):
        super().__init__(
            message=f"LLM call failed: {reason}",
            code="LLM_ERROR",
        )
