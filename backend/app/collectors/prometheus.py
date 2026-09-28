"""Prometheus metrics collector."""

import logging
from datetime import datetime, timezone

import httpx

from ..schemas.evidence import NormalizedEvent
from .base import BaseCollector

logger = logging.getLogger("incident-backend")


class PrometheusCollector(BaseCollector):
    """Collector for Prometheus metrics.

    Retrieves CPU, memory, request rate, error rate, and latency metrics.
    Metric query templates are configurable per deployment.
    """

    # Default metric query templates — override via subclass or config
    DEFAULT_QUERIES = {
        "request_rate": (
            'rate(app_http_request_count_total{{service_name="{service}"}}[5m])'
        ),
        "error_rate": (
            'rate(app_http_request_count_total{{service_name="{service}",http_status_code=~"5.."}}[5m])'
        ),
        "request_latency": (
            'histogram_quantile(0.95, rate('
            'app_http_request_duration_seconds_bucket'
            '{{service_name="{service}"}}[5m]))'
        ),
    }

    async def collect(
        self,
        service: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[NormalizedEvent]:
        """Collect all configured metrics for a service."""
        events: list[NormalizedEvent] = []

        for metric_name, query_template in self.DEFAULT_QUERIES.items():
            query = query_template.format(service=service)
            try:
                results = await self.query_range(
                    query=query,
                    start=start_time,
                    end=end_time,
                    step="60s",
                )
                events.extend(
                    self._to_events(results, service, metric_name)
                )
            except Exception as exc:
                logger.warning(
                    "Prometheus query failed metric=%s: %s",
                    metric_name,
                    exc,
                )

        return events

    async def query_prometheus(
        self,
        query: str,
        time: datetime | None = None,
    ) -> dict:
        """Execute an instant query against Prometheus."""
        params: dict = {"query": query}
        if time is not None:
            params["time"] = time.isoformat()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/query",
                params=params,
            )
            response.raise_for_status()
            return response.json()

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "60s",
    ) -> dict:
        """Execute a range query against Prometheus."""
        params = {
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": step,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/v1/query_range",
                params=params,
            )
            response.raise_for_status()
            return response.json()

    # ----- Convenience helpers -----

    async def get_service_cpu(self, service: str) -> dict:
        """Get current CPU usage for a service."""
        query = self.DEFAULT_QUERIES["cpu_usage"].format(service=service)
        return await self.query_prometheus(query)

    async def get_service_memory(self, service: str) -> dict:
        """Get current memory usage for a service."""
        query = self.DEFAULT_QUERIES["memory_usage"].format(service=service)
        return await self.query_prometheus(query)

    async def get_request_rate(self, service: str) -> dict:
        """Get current request rate for a service."""
        query = self.DEFAULT_QUERIES["request_rate"].format(service=service)
        return await self.query_prometheus(query)

    async def get_error_rate(self, service: str) -> dict:
        """Get current error rate for a service."""
        query = self.DEFAULT_QUERIES["error_rate"].format(service=service)
        return await self.query_prometheus(query)

    async def query_scalar(
        self, query: str, default: float | None = None
    ) -> float | None:
        """Query Prometheus for a single scalar value."""
        try:
            res = await self.query_prometheus(query)
            if res.get("status") == "success":
                results = res.get("data", {}).get("result", [])
                if results and len(results) > 0:
                    val_pair = results[0].get("value")
                    if val_pair and len(val_pair) > 1:
                        val = float(val_pair[1])
                        if val == val:  # Check not NaN
                            return val
        except Exception as exc:
            logger.debug("Prometheus query_scalar failed query=%s: %s", query, exc)
        return default

    async def get_discovered_services(self) -> list[str]:
        """Dynamically discover active service names from Prometheus metrics."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/label/service_name/values"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        values = data.get("data", [])
                        if values:
                            return sorted(values)
        except Exception as exc:
            logger.debug("Prometheus get_discovered_services failed: %s", exc)
        return []

    async def health_check(self) -> bool:
        """Check if Prometheus is reachable on base_url or fallback URL."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/-/healthy")
                if response.status_code == 200:
                    return True
        except Exception:
            pass

        # Try fallback URL if base_url is unreachable (e.g., localhost vs container hostname)
        fallback_url = (
            "http://localhost:9090"
            if "prometheus" in self.base_url
            else "http://prometheus:9090"
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{fallback_url}/-/healthy")
                if response.status_code == 200:
                    self.base_url = fallback_url
                    return True
        except Exception:
            pass

        return False

    async def query_range_values(
        self, query: str, duration_seconds: int = 900, step: str = "60s"
    ) -> list[float]:
        """Execute a range query against Prometheus and return numeric values for sparklines."""
        try:
            end_dt = datetime.now(timezone.utc)
            start_dt = datetime.fromtimestamp(
                end_dt.timestamp() - duration_seconds, tz=timezone.utc
            )
            res = await self.query_range(query, start=start_dt, end=end_dt, step=step)
            if res.get("status") == "success":
                results = res.get("data", {}).get("result", [])
                if results and len(results) > 0:
                    raw_values = results[0].get("values", [])
                    out: list[float] = []
                    for pair in raw_values:
                        try:
                            val = float(pair[1])
                            if val == val:  # Check not NaN
                                out.append(round(val, 2))
                        except (ValueError, TypeError):
                            continue
                    return out
        except Exception as exc:
            logger.debug("Prometheus query_range_values failed: %s", exc)
        return []

    async def get_prometheus_alert_rules(self) -> list[dict]:
        """Fetch alert rules and active alerts from Prometheus API."""
        rules: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{self.base_url}/api/v1/rules")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("status") == "success":
                        groups = data.get("data", {}).get("groups", [])
                        for group in groups:
                            for r in group.get("rules", []):
                                if r.get("type") == "alerting":
                                    rules.append(
                                        {
                                            "name": r.get("name", "AlertRule"),
                                            "query": r.get("query", ""),
                                            "severity": r.get("labels", {})
                                            .get("severity", "info")
                                            .upper(),
                                            "status": r.get("state", "ok").upper(),
                                        }
                                    )
        except Exception as exc:
            logger.debug("Prometheus get_prometheus_alert_rules failed: %s", exc)
        return rules



    # ----- Internal helpers -----

    def _to_events(
        self,
        response: dict,
        service: str,
        metric_name: str,
    ) -> list[NormalizedEvent]:
        """Convert a Prometheus API response to normalized events."""
        events: list[NormalizedEvent] = []

        if response.get("status") != "success":
            return events

        results = response.get("data", {}).get("result", [])

        for result in results:
            metric_labels = result.get("metric", {})
            values = result.get("values", [])

            # Handle instant-query format (single "value" instead of "values")
            if not values:
                value_pair = result.get("value")
                if value_pair:
                    values = [value_pair]

            for ts, value in values:
                try:
                    float_value = float(value)
                except (ValueError, TypeError):
                    continue

                severity = self._determine_severity(metric_name, float_value)

                events.append(
                    NormalizedEvent(
                        timestamp=datetime.fromtimestamp(float(ts)),
                        source="prometheus",
                        service=service,
                        event_type=metric_name,
                        severity=severity,
                        content=f"{metric_name} = {float_value:.4f}",
                        metadata={
                            "value": float_value,
                            "labels": metric_labels,
                        },
                    )
                )

        return events

    @staticmethod
    def _determine_severity(metric_name: str, value: float) -> str:
        """Determine severity based on metric type and value thresholds."""
        thresholds: dict[str, dict[str, float]] = {
            "cpu_usage": {"warning": 0.7, "error": 0.9, "critical": 0.95},
            "memory_usage": {
                "warning": 0.7e9,
                "error": 0.9e9,
                "critical": 0.95e9,
            },
            "error_rate": {"warning": 0.01, "error": 0.05, "critical": 0.1},
            "request_latency": {
                "warning": 1.0,
                "error": 3.0,
                "critical": 5.0,
            },
        }

        levels = thresholds.get(metric_name, {})
        if levels.get("critical") and value >= levels["critical"]:
            return "critical"
        if levels.get("error") and value >= levels["error"]:
            return "error"
        if levels.get("warning") and value >= levels["warning"]:
            return "warning"
        return "info"
