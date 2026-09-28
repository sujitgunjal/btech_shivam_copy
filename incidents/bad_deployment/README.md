# Incident: bad_deployment

## Purpose
Simulate a deployment that introduces a defect.

## Affected Service
Application compose service.

## Severity
HIGH

## Expected Root Cause (GROUND TRUTH)
Defective code/config shipped in the most recent deployment.

## Expected Symptoms
Error-rate step change tied to deployment time.

## Expected Evidence
- `deployments/deployment_history.json` entry with matching timestamp
- Backend error logs
- Prometheus error counter step

## Timeline
T+0 baseline → T+2 bad deploy → T+10 errors → T+120 rollback → T+130 recovered.

## How to Run
```bash
python incidents/bad_deployment/simulate.py --service order-service --duration 120