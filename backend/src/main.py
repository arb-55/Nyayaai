"""
NyayaAI Backend — FastAPI Application Entry Point

Sets up:
- CORS middleware
- Exception handlers
- Router registration
- Health check endpoint
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.exceptions import NyayaAIException
from src.routers import cases, documents, analysis, reports


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: ensure upload directory exists
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: cleanup if needed


# ── App ──
app = FastAPI(
    title="NyayaAI",
    description=(
        "AI-Assisted Multi-Agent Legal Document Analysis System for Indian Court Cases. "
        "This is an assistive analytical tool — it does NOT replace judges or make legally binding decisions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception Handlers ──
@app.exception_handler(NyayaAIException)
async def nyayaai_exception_handler(request: Request, exc: NyayaAIException):
    """Convert NyayaAI exceptions to standardized JSON error responses."""
    # Map error codes to HTTP status codes
    status_map = {
        "CASE_NOT_FOUND": 404,
        "DOCUMENT_NOT_FOUND": 404,
        "ANALYSIS_NOT_FOUND": 404,
        "FILE_TOO_LARGE": 413,
        "PDF_EXTRACTION_FAILED": 422,
        "ANALYSIS_ALREADY_RUNNING": 409,
        "LLM_ERROR": 502,
    }
    status_code = status_map.get(exc.code, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ── Routers ──
app.include_router(cases.router, prefix="/api/v1", tags=["Cases"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])


# ── Health Check ──
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "NyayaAI Backend",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
