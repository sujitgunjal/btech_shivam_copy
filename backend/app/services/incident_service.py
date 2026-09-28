"""Business logic for incident management."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.evidence import Evidence
from ..models.incident import Incident
from ..schemas.incident import IncidentCreate, IncidentUpdate

logger = logging.getLogger("incident-backend")


class IncidentService:
    """Service layer for incident CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: IncidentCreate) -> Incident:
        """Create a new incident with auto-generated external_id."""
        incident = Incident(
            external_id="PENDING",  # placeholder, replaced after insert
            title=data.title,
            description=data.description,
            service=data.service,
            severity=data.severity,
            status="created",
            start_time=data.start_time,
            end_time=data.end_time,
            p99_latency_ms=data.p99_latency_ms,
            error_rate=data.error_rate,
            captured_at=data.captured_at or data.start_time,
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        # Generate external_id from the auto-incremented primary key
        incident.external_id = f"INC-{incident.id:04d}"
        self.db.commit()
        self.db.refresh(incident)

        return incident

    def get(self, incident_id: int) -> Incident | None:
        """Get a single incident by ID."""
        return (
            self.db.query(Incident)
            .filter(Incident.id == incident_id)
            .first()
        )

    def list_incidents(
        self,
        status: Optional[str] = None,
        service: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list[Incident]:
        """List incidents with optional filters."""
        query = self.db.query(Incident)

        if status:
            query = query.filter(Incident.status == status)
        if service:
            query = query.filter(Incident.service == service)
        if severity:
            query = query.filter(Incident.severity == severity)

        return query.order_by(Incident.created_at.desc()).all()

    def update(
        self, incident_id: int, data: IncidentUpdate
    ) -> Incident | None:
        """Update an existing incident."""
        incident = self.get(incident_id)
        if incident is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(incident, field, value)

        incident.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def resolve(self, incident_id: int) -> Incident | None:
        """Mark an incident as resolved."""
        incident = self.get(incident_id)
        if incident is None:
            return None

        incident.status = "resolved"
        incident.end_time = incident.end_time or datetime.now(timezone.utc)
        incident.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_evidence(self, incident_id: int) -> list[Evidence]:
        """Get all evidence for an incident."""
        return (
            self.db.query(Evidence)
            .filter(Evidence.incident_id == incident_id)
            .order_by(Evidence.timestamp.asc())
            .all()
        )
