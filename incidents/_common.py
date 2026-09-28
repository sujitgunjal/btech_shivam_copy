"""
Shared utilities for incident simulations.

Design goals:
- Zero required third-party dependencies (pyyaml optional; stdlib fallback).
- Never hard-code service/container names: discover from docker-compose.yml.
- Never run destructive Docker commands.
- Always leave a recoverable state trail.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger("incident")


# --------------------------------------------------------------------------- #
# Project root discovery
# --------------------------------------------------------------------------- #
def find_project_root(start: Path | None = None) -> Path:
    """Walk upward until a docker-compose.yml is found."""
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / "docker-compose.yml").is_file():
            return parent
    raise FileNotFoundError(
        "docker-compose.yml not found. Run this from inside the project tree."
    )


# --------------------------------------------------------------------------- #
# Minimal docker-compose parser (stdlib fallback)
# --------------------------------------------------------------------------- #
def _parse_compose_minimal(text: str) -> dict[str, Any]:
    """
    Very small YAML subset parser sufficient for extracting `services:` keys
    and simple scalar fields. Prefer pyyaml if available.
    """
    services: dict[str, dict[str, Any]] = {}
    in_services = False
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if re.match(r"^services\s*:\s*$", line):
            in_services = True
            continue
        if in_services and re.match(r"^[A-Za-z]", line):  # top-level key again
            in_services = False
        if not in_services:
            continue
        m = re.match(r"^  ([A-Za-z0-9_.-]+)\s*:\s*$", line)
        if m:
            current = m.group(1)
            services[current] = {}
            continue
        m = re.match(r"^    ([A-Za-z0-9_.-]+)\s*:\s*(.+?)\s*$", line)
        if m and current:
            services[current][m.group(1)] = m.group(2).strip("'\"")
    return {"services": services}


def load_compose(root: Path | None = None) -> dict[str, Any]:
    root = root or find_project_root()
    compose_path = root / "docker-compose.yml"
    text = compose_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except Exception:
        return _parse_compose_minimal(text)


def compose_service_names(root: Path | None = None) -> list[str]:
    return sorted(load_compose(root).get("services", {}).keys())


def discover_service(
    role: str,
    root: Path | None = None,
    explicit: str | None = None,
) -> str:
    """
    Resolve a logical role ("postgres", "app") to a real compose service name.

    If `explicit` is provided (env var / CLI), it wins.
    Otherwise, heuristics are applied over the actual compose services.
    Raises a clear error listing what WAS found if nothing matches.
    """
    if explicit:
        return explicit
    services = compose_service_names(root)
    if not services:
        raise RuntimeError("No services found in docker-compose.yml.")

    patterns = {
        "postgres": [r"postgres", r"db", r"database"],
        "app": [r"order", r"api", r"backend", r"app", r"service"],
    }
    for pat in patterns.get(role, []):
        for name in services:
            if re.search(pat, name, re.IGNORECASE):
                return name
    raise RuntimeError(
        f"Could not auto-detect a service for role={role!r}. "
        f"Available services: {services}. "
        f"Pass --service or set INCIDENT_{role.upper()}_SERVICE."
    )


# --------------------------------------------------------------------------- #
# Docker CLI wrappers (safe subset)
# --------------------------------------------------------------------------- #
def run(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    log.debug("$ %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
    )


def docker_available() -> bool:
    try:
        run(["docker", "version", "--format", "{{.Server.Version}}"])
        return True
    except Exception:
        return False


def container_id(service: str, root: Path | None = None) -> str | None:
    """Resolve compose service -> running container id."""
    root = root or find_project_root()
    try:
        cp = run(
            ["docker", "compose", "ps", "-q", service],
            check=False,
        )
        cid = cp.stdout.strip().splitlines()
        return cid[0] if cid else None
    except Exception:
        return None


def pause_container(cid: str) -> None:
    run(["docker", "pause", cid])


def unpause_container(cid: str) -> None:
    run(["docker", "unpause", cid])


def exec_in_container(cid: str, argv: list[str], detach: bool = False) -> subprocess.CompletedProcess:
    base = ["docker", "exec"]
    if detach:
        base.append("-d")
    base.append(cid)
    base.extend(argv)
    return run(base, check=False)


# --------------------------------------------------------------------------- #
# State guard: makes every incident recoverable even after Ctrl+C / crash
# --------------------------------------------------------------------------- #
STATE_DIR = Path(__file__).resolve().parent / ".state"


@dataclass
class IncidentState:
    incident_id: str
    incident_type: str
    target_service: str
    container_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)

    def path(self) -> Path:
        STATE_DIR.mkdir(exist_ok=True)
        return STATE_DIR / f"{self.incident_type}.json"

    def save(self) -> None:
        self.path().write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")

    def clear(self) -> None:
        try:
            self.path().unlink()
        except FileNotFoundError:
            pass

    @classmethod
    def load(cls, incident_type: str) -> "IncidentState | None":
        p = STATE_DIR / f"{incident_type}.json"
        if not p.is_file():
            return None
        return cls(**json.loads(p.read_text(encoding="utf-8")))


# --------------------------------------------------------------------------- #
# Argparse + graceful shutdown boilerplate
# --------------------------------------------------------------------------- #
def base_argparser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--service", help="Override auto-detected compose service name.")
    p.add_argument("--duration", type=int, default=90,
                   help="Incident duration in seconds (default 90, max 600).")
    p.add_argument("--intensity", type=float, default=1.0,
                   help="Relative intensity (default 1.0).")
    p.add_argument("--recover", action="store_true",
                   help="Recover from a previously interrupted run and exit.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print planned actions without executing them.")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def clamp_duration(seconds: int, maximum: int = 600) -> int:
    return max(1, min(seconds, maximum))


class GracefulExit:
    """Context manager that always runs cleanup on normal exit, Ctrl+C or SIGTERM."""

    def __init__(self) -> None:
        self._fired = False

    def __enter__(self) -> "GracefulExit":
        def handler(signum, frame):
            if not self._fired:
                self._fired = True
                log.warning("Signal %s received — recovering…", signum)
                raise KeyboardInterrupt
        signal.signal(signal.SIGINT, handler)
        try:
            signal.signal(signal.SIGTERM, handler)
        except (AttributeError, ValueError):
            pass
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is KeyboardInterrupt:
            log.info("Interrupted — cleanup will run.")
            return True
        return False


# --------------------------------------------------------------------------- #
# Pretty status output
# --------------------------------------------------------------------------- #
def banner(incident_id: str, incident_type: str, service: str, phase: str) -> None:
    line = f"[{phase}] {incident_id} ({incident_type}) -> {service}"
    log.info(line)


def emit_phase(phase: str, **kwargs: Any) -> None:
    payload = {"phase": phase, **kwargs}
    print(json.dumps(payload), flush=True)