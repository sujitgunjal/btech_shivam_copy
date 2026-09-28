"""Jaeger distributed tracing collector."""

import logging
from datetime import datetime

import httpx

from ..schemas.evidence import NormalizedEvent
from .base import BaseCollector

logger = logging.getLogger("incident-backend")


class JaegerCollector(BaseCollector):
    """Collector for Jaeger distributed traces.

    Retrieves traces and spans for a service, detects errors
    from span tags and logs, and normalizes into NormalizedEvent instances.
    """

    async def collect(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[NormalizedEvent]:
        """Collect traces for the given service and time window."""
        return await self.get_traces(service, start_time, end_time)

    async def get_traces(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 20,
    ) -> list[NormalizedEvent]:
        """Retrieve traces from Jaeger."""
        params = {
            "service": service,
            "start": str(int(start_time.timestamp() * 1_000_000)),
            "end": str(int(end_time.timestamp() * 1_000_000)),
            "limit": limit,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/traces",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, service)

    async def get_trace(self, trace_id: str) -> dict:
        """Retrieve a single trace by ID."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/traces/{trace_id}",
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Check if Jaeger is reachable."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/services"
                )
                return response.status_code == 200
        except Exception:
            return False

    # ----- Internal helpers -----

    def _parse_response(
        self,
        data: dict,
        service: str,
    ) -> list[NormalizedEvent]:
        """Parse Jaeger traces response into normalized events."""
        events: list[NormalizedEvent] = []
        traces = data.get("data", [])

        for trace in traces:
            trace_id = trace.get("traceID", "unknown")
            spans = trace.get("spans", [])

            for span in spans:
                span_id = span.get("spanID", "unknown")
                operation = span.get("operationName", "unknown")
                start_us = span.get("startTime", 0)
                duration_us = span.get("duration", 0)

                try:
                    timestamp = datetime.fromtimestamp(start_us / 1_000_000)
                except (ValueError, TypeError, OSError):
                    continue

                has_error = self._span_has_error(span)
                severity = "error" if has_error else "info"
                duration_ms = duration_us / 1_000

                content = (
                    f"Span {operation} "
                    f"duration={duration_ms:.1f}ms "
                    f"trace={trace_id}"
                )

                if has_error:
                    error_msg = self._extract_error_message(span)
                    if error_msg:
                        content += f" error={error_msg}"

                events.append(
                    NormalizedEvent(
                        timestamp=timestamp,
                        source="jaeger",
                        service=service,
                        event_type="trace",
                        severity=severity,
                        content=content,
                        metadata={
                            "trace_id": trace_id,
                            "span_id": span_id,
                            "operation": operation,
                            "duration_us": duration_us,
                            "duration_ms": duration_ms,
                            "tags": {
                                t["key"]: t.get("value")
                                for t in span.get("tags", [])
                            },
                        },
                    )
                )

        return events

    @staticmethod
    def _span_has_error(span: dict) -> bool:
        """Check if a span has error tags."""
        for tag in span.get("tags", []):
            if tag.get("key") == "error" and tag.get("value") is True:
                return True
            if (
                tag.get("key") == "otel.status_code"
                and tag.get("value") == "ERROR"
            ):
                return True
            if tag.get("key") == "http.status_code":
                try:
                    if int(tag["value"]) >= 500:
                        return True
                except (ValueError, TypeError):
                    pass
        return False

    @staticmethod
    def _extract_error_message(span: dict) -> str | None:
        """Extract error message from span logs."""
        for log_entry in span.get("logs", []):
            for field in log_entry.get("fields", []):
                if field.get("key") in (
                    "message",
                    "error",
                    "error.message",
                ):
                    return str(field.get("value", ""))
        return None
