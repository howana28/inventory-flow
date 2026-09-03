# Architecture

InventoryFlow is split into a static Next.js frontend and a FastAPI application. In production the frontend is exported at build time and served by FastAPI, which keeps deployment to one service and one public URL.

```text
Browser
   │
   ▼
Next.js static UI
   │  /api/v1/*
   ▼
FastAPI
   ├── Authentication / RBAC
   ├── Inventory services
   ├── Concurrency locks + heartbeat
   ├── Validation / recount workflow
   ├── Audit trail
   └── ERP adapter
          ├── Demo provider
          └── Bling OAuth 2.0 provider
   │
   ▼
SQLAlchemy
   ├── SQLite (local demo)
   └── PostgreSQL / Supabase-compatible connection
```

## Inventory lifecycle

1. Synchronize catalog from the active ERP provider.
2. Create an immutable inventory snapshot.
3. Operators reserve zones and count products by SKU/EAN.
4. All zones must be finalized before validation.
5. Difference is calculated as `physical count - system snapshot`.
6. Divergences can be approved or sent to recount.
7. Recount work is reserved per SKU to prevent duplicate work.
8. An inventory can be closed only after all items have a final resolution.

## Concurrency

`resource_locks` provides a generic lock model with three identifiers: inventory, scope and resource. Counting uses `scope=COUNTING, resource=<zone>`. Recount uses `scope=RECOUNT, resource=<sku>`. Locks are bound to the authenticated user and a browser session ID, refreshed through heartbeat, and expire after prolonged inactivity.
