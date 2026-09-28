"""Pydantic schemas for investigation endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InvestigationResponse(BaseModel):
    """Schema for investigation API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    evidence_count: int = 0
