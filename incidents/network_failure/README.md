# Incident: network_failure

## Purpose
Simulate a network/dependency failure affecting one service.

## Affected Service
Application compose service.

## Severity
HIGH

## Expected Root Cause (GROUND TRUTH)
Egress from the target container is blocked.

## Expected Symptoms
Timeouts, 5xx, missing dependency spans.

## Expected Evidence
Jaeger gaps, upstream 5xx counters, timeout log lines.

## Timeline
T+0 baseline → T+2 block → T+90 restore → T+95 recovered.

## How to Run
```bash
python incidents/network_failure/simulate.py --service order-service --duration 90