"""Telemetry collection orchestration.

This service wraps the three collectors and provides a single
entry point for gathering all telemetry.  It is also the seam
where future RAG/embedding steps will be inserted.
"""

import asyncio
import logging
from datetime import datetime

from ..collectors.jaeger import JaegerCollector
from ..collectors.loki import LokiCollector
from ..collectors.prometheus import PrometheusCollector
from ..config import get_settings
from ..schemas.evidence import NormalizedEvent

logger = logging.getLogger("incident-backend")


class TelemetryService:
    """Orchestrates concurrent telemetry collection from all sources."""

    def __init__(self) -> None:
        settings = get_settings()
        self.prometheus = PrometheusCollector(
            settings.PROMETHEUS_URL, settings.COLLECTOR_TIMEOUT
        )
        self.loki = LokiCollector(
            settings.LOKI_URL, settings.COLLECTOR_TIMEOUT
        )
        self.jaeger = JaegerCollector(
            settings.JAEGER_URL, settings.COLLECTOR_TIMEOUT
        )

    async def collect_all(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[list[NormalizedEvent], list[dict]]:
        """Collect telemetry from all sources concurrently.

        Returns:
            A tuple of ``(events, errors)`` where *events* is a flat
            list of :class:`NormalizedEvent` and *errors* is a list of
            dicts describing collector failures.
        """
        all_events: list[NormalizedEvent] = []
        all_errors: list[dict] = []

        results = await asyncio.gather(
            self._safe_collect(
                "prometheus", self.prometheus, service, start_time, end_time
            ),
            self._safe_collect(
                "loki", self.loki, service, start_time, end_time
            ),
            self._safe_collect(
                "jaeger", self.jaeger, service, start_time, end_time
            ),
        )

        for events, errors in results:
            all_events.extend(events)
            all_errors.extend(errors)

        return all_events, all_errors

    async def _safe_collect(
        self,
        source_name: str,
        collector,
        service: str,
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[list[NormalizedEvent], list[dict]]:
        """Collect from a single source, catching all errors."""
        try:
            logger.info(
                "Starting %s collection for service=%s",
                source_name,
                service,
            )
            events = await collector.collect(service, start_time, end_time)
            logger.info(
                "%s collection completed records=%d",
                source_name,
                len(events),
            )
            return events, []
        except Exception as exc:
            logger.warning(
                "%s collection failed: %s", source_name, exc
            )
            return [], [
                {
                    "source": source_name,
                    "message": f"{source_name} unavailable: {exc}",
                    "error_type": type(exc).__name__,
                }
            ]
