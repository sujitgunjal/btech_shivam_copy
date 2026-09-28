# Incident: memory_spike

## Purpose
Temporarily raise memory usage inside one container.

## Affected Service
Application compose service.

## Severity
HIGH

## Expected Root Cause (GROUND TRUTH)
Injected allocation inside the target container.

## Expected Symptoms
Rising `container_memory_working_set_bytes`, possible OOMKill.

## Expected Evidence
cAdvisor memory series, kernel OOM log if limit exceeded.

## Timeline
T+0 baseline → T+5 alloc → T+90 release → T+95 recovered.

## How to Run
```bash
python incidents/memory_spike/simulate.py --service order-service --mb 200 --duration 90