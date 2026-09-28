# Incident: high_latency

## Purpose
Inject artificial latency into one service.

## Affected Service
Application compose service (auto-detected, override with `--service`).

## Severity
MEDIUM

## Expected Root Cause (GROUND TRUTH)
Network delay injected via `tc netem` inside the target container.

## Expected Symptoms
- p99 latency ~2s
- client timeouts
- slow traces

## Expected Evidence
Prometheus latency histogram shift, Jaeger spans.

## Timeline
T+0 baseline → T+2 delay applied → T+90 removed → T+95 recovered.

## How to Run
```bash
python incidents/high_latency/simulate.py --service order-service --delay-ms 2000 --duration 90