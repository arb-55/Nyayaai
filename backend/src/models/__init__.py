"""
NyayaAI Models Package

Import all models here so Alembic and SQLAlchemy can discover them.
"""

from src.models.case import Case
from src.models.document import Document
from src.models.entity import ExtractedEntity
from src.models.analysis import Analysis
from src.models.finding import AgentFinding, ConsensusReport

__all__ = [
    "Case",
    "Document",
    "ExtractedEntity",
    "Analysis",
    "AgentFinding",
    "ConsensusReport",
]
