"""
Document Service — PDF text extraction and NLP text cleaning.

Implements Phase 2 functionality:
- Extract text from uploaded PDFs using pdfplumber page by page
- Clean and normalize extracted text without altering legal wording
"""

import logging
import re
from pathlib import Path

import pdfplumber

from src.core.exceptions import PDFExtractionError

logger = logging.getLogger(__name__)


class DocumentService:
    """Handles PDF processing, text extraction, and text cleaning."""

    async def extract_text(self, file_path: str) -> dict:
        """
        Extract text from a PDF file using pdfplumber page by page.

        Args:
            file_path: Absolute or relative path to the PDF file on disk.

        Returns:
            dict containing:
                - text: Full raw extracted text string across all pages
                - page_count: Total number of pages in the PDF
                - pages: List of {"page_number": int, "text": str} dicts

        Raises:
            PDFExtractionError: If pdfplumber cannot open or parse the PDF.
        """
        file = Path(file_path)
        if not file.exists():
            raise PDFExtractionError(file.name, "File does not exist on disk")

        raw_pages = []
        page_count = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                if page_count == 0:
                    return {"text": "", "page_count": 0, "pages": []}

                for i, page in enumerate(pdf.pages, start=1):
                    try:
                        extracted = page.extract_text()
                        page_text = extracted.strip() if extracted else ""
                    except Exception as page_err:
                        logger.warning(
                            f"Error extracting page {i} of '{file.name}': {page_err}"
                        )
                        page_text = ""

                    raw_pages.append({"page_number": i, "text": page_text})

        except Exception as pdf_err:
            logger.error(f"pdfplumber failed for '{file.name}': {pdf_err}")
            raise PDFExtractionError(file.name, str(pdf_err))

        # Join pages with clear page markers
        page_blocks = []
        for p in raw_pages:
            if p["text"]:
                page_blocks.append(f"[Page {p['page_number']}]\n{p['text']}")

        full_text = "\n\n".join(page_blocks)

        return {
            "text": full_text,
            "page_count": page_count,
            "pages": raw_pages,
        }

    def clean_text(self, raw_text: str | None) -> str:
        """
        Clean and normalize extracted text.

        Operations:
        - Normalize line endings (\r\n -> \n)
        - Strip trailing whitespace from lines
        - Collapse 3+ consecutive newlines to 2 newlines (preserve paragraphs)
        - Remove null bytes and ASCII control characters (0x00 - 0x08, 0x0B - 0x0C, 0x0E - 0x1F)
        - Preserve legal wording, numbers, punctuation, section numbers, and Devanagari text

        Args:
            raw_text: Raw text string from PDF extraction.

        Returns:
            Cleaned text string.
        """
        if not raw_text:
            return ""

        # Remove control characters except \t and \n
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)

        # Normalize line endings
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # Strip trailing space on each line
        lines = [line.rstrip() for line in cleaned.split("\n")]
        cleaned = "\n".join(lines)

        # Collapse multiple empty lines (3 or more newlines reduced to 2)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()


# Singleton instance
document_service = DocumentService()
