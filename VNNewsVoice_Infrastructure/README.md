# VNNewsVoice_Infrastructure

## DevOps Artifacts

- `docker-compose.infra.yml`: local/shared infrastructure stack (PostgreSQL, RabbitMQ, Qdrant, Redis, MinIO, MLflow).
- `PHASE3_GHCR_VERIFICATION.md`: checklist and evidence table for GHCR publish verification across 8 services.
- `PHASE5_STAGING_SMOKE_RUNBOOK.md`: runbook for staging smoke tests.
- `scripts/staging-smoke-tests.ps1`: PowerShell smoke checks (Gateway health, Auth JWKS, RAG health, optional RabbitMQ API).
- `scripts/staging-smoke-tests.sh`: Bash smoke checks for Linux runners.
- `.github/workflows/staging-smoke.yml`: manual workflow to execute staging smoke tests via `workflow_dispatch`.
- `.github/workflows/staging-cd.yml`: staging CD skeleton (trigger `develop` + manual), includes optional deploy step and integrated smoke tests.