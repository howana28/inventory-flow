# API overview

FastAPI exposes interactive documentation at `/api/docs` and the OpenAPI schema at `/api/openapi.json`.

Primary groups:

- `/api/v1/auth/*` — login, logout and current user.
- `/api/v1/dashboard` — operational summary.
- `/api/v1/preparation/*` — catalog sync and inventory preparation.
- `/api/v1/counting/*` — zones, reservations, heartbeat and barcode/SKU counts.
- `/api/v1/validation/*` — reconciliation, approval and recount requests.
- `/api/v1/recounts/*` — per-SKU reservation, heartbeat and recount submission.
- `/api/v1/history/*` — inventories and audit trail.
- `/api/v1/users/*` — RBAC administration.
- `/api/v1/integrations/*` — safe connection status, ERP sync, demo scenarios and optional Bling OAuth.

A generated OpenAPI snapshot is stored in `docs/openapi.json` for portfolio review.
