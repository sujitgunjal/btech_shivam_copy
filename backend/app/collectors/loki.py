"""Loki log collector."""

import logging
from datetime import datetime

import httpx

from ..schemas.evidence import NormalizedEvent
from .base import BaseCollector

logger = logging.getLogger("incident-backend")


class LokiCollector(BaseCollector):
    """Collector for Loki logs.

    Retrieves log entries for a given service and time window,
    auto-detects severity from log content, and normalizes
    into NormalizedEvent instances.
    """

    async def collect(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[NormalizedEvent]:
        """Collect logs for the given service and time window."""
        query = f'{{service_name="{service}"}}'
        return await self.query_logs(
            service=service,
            start_time=start_time,
            end_time=end_time,
            query=query,
        )

    async def query_logs(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
        query: str | None = None,
        limit: int = 100,
    ) -> list[NormalizedEvent]:
        """Query Loki for log entries."""
        if query is None:
            query = f'{{container=~".*{service}.*"}}'

        params = {
            "query": query,
            "start": str(int(start_time.timestamp() * 1_000_000_000)),
            "end": str(int(end_time.timestamp() * 1_000_000_000)),
            "limit": limit,
            "direction": "backward",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/loki/api/v1/query_range",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, service)

    async def health_check(self) -> bool:
        """Check if Loki is reachable."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/ready")
                return response.status_code == 200
        except Exception:
            return False

    # ----- Internal helpers -----

    def _parse_response(
        self,
        data: dict,
        service: str,
    ) -> list[NormalizedEvent]:
        """Parse Loki query_range response into normalized events."""
        events: list[NormalizedEvent] = []

        results = data.get("data", {}).get("result", [])

        for stream in results:
            labels = stream.get("stream", {})
            values = stream.get("values", [])

            for ts_ns, line in values:
                try:
                    timestamp = datetime.fromtimestamp(
                        int(ts_ns) / 1_000_000_000
                    )
                except (ValueError, TypeError, OSError):
                    continue

                severity = self._detect_severity(line)

                events.append(
                    NormalizedEvent(
                        timestamp=timestamp,
                        source="loki",
                        service=service,
                        event_type="log_entry",
                        severity=severity,
                        content=line,
                        metadata={"labels": labels},
                    )
                )

        return events

    @staticmethod
    def _detect_severity(log_line: str) -> str:
        """Detect severity from log line content."""
        upper = log_line.upper()
        if "CRITICAL" in upper or "FATAL" in upper:
            return "critical"
        if "ERROR" in upper or "EXCEPTION" in upper:
            return "error"
        if "WARN" in upper:
            return "warning"
        return "info"
