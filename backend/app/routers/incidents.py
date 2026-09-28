"""Incident management endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.evidence import EvidenceResponse
from ..schemas.incident import (
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
)
from ..schemas.investigation import InvestigationResponse
from ..services.incident_service import IncidentService
from ..services.investigation_service import InvestigationService

logger = logging.getLogger("incident-backend")

router = APIRouter()


@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
):
    """Create a new incident."""
    svc = IncidentService(db)
    incident = svc.create(incident_data)
    logger.info(
        "Incident created id=%s external_id=%s",
        incident.id,
        incident.external_id,
    )
    return incident


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List incidents with optional filters."""
    svc = IncidentService(db)
    incidents = svc.list_incidents(status=status, service=service, severity=severity)
    return IncidentListResponse(incidents=incidents, total=len(incidents))


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    """Get a single incident by ID."""
    svc = IncidentService(db)
    incident = svc.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    update_data: IncidentUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an incident."""
    svc = IncidentService(db)
    incident = svc.update(incident_id, update_data)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    logger.info("Incident updated id=%s", incident_id)
    return incident


@router.post(
    "/{incident_id}/resolve", response_model=IncidentResponse
)
def resolve_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    """Mark an incident as resolved."""
    svc = IncidentService(db)
    incident = svc.resolve(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    logger.info("Incident resolved id=%s", incident_id)
    return incident


@router.post(
    "/{incident_id}/investigate",
    response_model=InvestigationResponse,
)
async def investigate_incident(
    incident_id: int,
    db: Session = Depends(get_db),
):
    """Trigger an investigation for an incident."""
    svc = IncidentService(db)
    incident = svc.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    inv_svc = InvestigationService(db)
    investigation = await inv_svc.start_investigation(incident)
    evidence_count = inv_svc.count_evidence(incident.id)

    logger.info(
        "Investigation completed id=%s incident_id=%s status=%s",
        investigation.id,
        incident_id,
        investigation.status,
    )

    return InvestigationResponse(
        id=investigation.id,
        incident_id=investigation.incident_id,
        status=investigation.status,
        started_at=investigation.started_at,
        completed_at=investigation.completed_at,
        report=investigation.report,
        confidence=investigation.confidence,
        created_at=investigation.created_at,
        evidence_count=evidence_count,
    )


@router.get(
    "/{incident_id}/evidence",
    response_model=list[EvidenceResponse],
)
def get_incident_evidence(
    incident_id: int,
    db: Session = Depends(get_db),
):
    """List all evidence for an incident."""
    svc = IncidentService(db)
    incident = svc.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return svc.get_evidence(incident_id)
