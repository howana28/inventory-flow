# InventoryFlow

**Multi-user warehouse inventory reconciliation platform.**

InventoryFlow is a portfolio-ready full-stack application for physical inventory operations. It demonstrates catalog snapshots, barcode/SKU counting, concurrent operator locks, validation, recount queues, audit history, role-based access, Excel exports and an ERP integration layer.

This repository contains **only synthetic demo data**. No company names, private catalogs, real stock quantities, user data, production URLs or credentials are included.

## Why this project exists

Spreadsheet-driven inventories become fragile when multiple people count at once. Operators can duplicate work, overwrite each other, lose track of locations, and create ambiguous recounts. InventoryFlow turns the process into a controlled workflow with explicit ownership and deterministic reconciliation.

```text
Catalog sync
    ↓
Immutable snapshot
    ↓
Multi-user zone counting
    ↓
Validation
    ↓
Difference = Physical Count - System Snapshot
    ↓
OK / SHORTAGE / SURPLUS
    ↓
Optional recount by reserved SKU
    ↓
Final resolution + audit history
```

## Tech stack

- **Frontend:** Next.js 16, React 19, TypeScript
- **Backend:** FastAPI, Python 3.12
- **Persistence:** SQLAlchemy; SQLite for zero-config demo, PostgreSQL/Supabase-compatible URL for hosted environments
- **Authentication:** opaque server-side sessions with HttpOnly cookies
- **Authorization:** backend-enforced RBAC permissions
- **ERP layer:** synthetic Demo Provider + optional Bling OAuth 2.0 provider
- **Exports:** OpenPyXL
- **Deployment:** Docker, single service / single public URL

## Main features

- Responsive dashboard with inventory progress.
- Immutable inventory snapshot before counting begins.
- Zone-based physical counting by SKU or EAN.
- Multi-operator reservation locks with heartbeat and TTL.
- F5-safe active zone and recount session restoration.
- Deterministic validation: `counted - system snapshot`.
- Divergence classification as shortage or surplus.
- Recount queue with one SKU reserved to one browser session at a time.
- Optional "Next item" workflow; no automatic loop.
- Manual divergence approval for supervised exceptions.
- Audit trail and historical inventory inspection.
- Excel validation export.
- User and permission administration.
- Admin-only Integrations module with safe database metadata, ERP status, sync metrics and sync history.
- Demo scenarios that jump directly to Counting, Validation or Recount states.
- Bling OAuth 2.0 implementation kept separate from the public demo provider.

## Demo accounts

The application seeds these fictional users on first start:

| Profile | E-mail | Password |
| --- | --- | --- |
| Administrator | `admin@inventoryflow.demo` | `Demo123!` |
| Supervisor | `supervisor@inventoryflow.demo` | `Demo123!` |
| Operator | `operator@inventoryflow.demo` | `Demo123!` |

The public demo should keep `ALLOW_EXTERNAL_CONNECTIONS=false`.

## Permissions

| Module | Operator | Supervisor | Admin |
| --- | :---: | :---: | :---: |
| Dashboard | ✓ | ✓ | ✓ |
| Prepare inventory |  | ✓ | ✓ |
| Counting | ✓ | ✓ | ✓ |
| Validation |  | ✓ | ✓ |
| Recount | ✓ | ✓ | ✓ |
| History |  | ✓ | ✓ |
| Users |  |  | ✓ |
| Integrations |  |  | ✓ |

Permissions are stored per user and checked in FastAPI dependencies. Hiding a menu item in the frontend is not treated as an authorization boundary.

## Demo dataset

The seed generator creates 420 fictional products distributed across 18 warehouse zones. Product names, brands, EAN-like identifiers, locations and quantities are deterministic synthetic values generated at runtime.

The **Integrations** screen includes three scenario buttons:

- **Counting:** several zones are already finalized and the remaining zones can be reserved and counted.
- **Validation:** all zones are finalized and the snapshot contains deliberate shortages/surpluses.
- **Recount:** selected divergent SKUs are already placed in the multi-operator recount queue.

This makes the application easy to demonstrate without manually completing hundreds of scans.

## Local setup — Windows PowerShell

### 1. Backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

The default database is SQLite and needs no external setup.

### 2. Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run build
```

Copy the static export to FastAPI:

```powershell
Remove-Item -Recurse -Force ..\backend\static -ErrorAction SilentlyContinue
Copy-Item -Recurse .\out ..\backend\static
```

### 3. Run

```powershell
cd ..\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 10000 --reload
```

Open `http://127.0.0.1:10000`.

API documentation is available at `http://127.0.0.1:10000/api/docs`.

## PostgreSQL / Supabase-compatible database

Change only the environment variable:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
```

The application creates its tables on startup. `database/schema.sql` is included as a readable reference for the core schema.

## ERP providers

### Demo Provider

Default configuration:

```env
ERP_PROVIDER=demo
ALLOW_EXTERNAL_CONNECTIONS=false
```

It loads the synthetic product catalog and is safe for a public portfolio deployment.

### Bling Provider

The Bling adapter is optional and no real credential is stored in this repository.

```env
ERP_PROVIDER=demo
ALLOW_EXTERNAL_CONNECTIONS=true
BLING_CLIENT_ID=
BLING_CLIENT_SECRET=
BLING_REDIRECT_URI=http://127.0.0.1:10000/api/v1/integrations/bling/callback
TOKEN_ENCRYPTION_KEY=
```

Generate a Fernet key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

When configured, the Integrations page can start the OAuth flow. Access/refresh tokens are encrypted before being persisted. For a public demo, leave external connections disabled.

## Concurrency model

A generic `resource_locks` table protects operational work:

```text
COUNTING
inventory + zone + user + browser session + expires_at

RECOUNT
inventory + SKU + user + browser session + expires_at
```

The same browser session can renew its own lock after F5. A different operator/session receives HTTP `409` until the lock is explicitly released or expires after inactivity.

## Security highlights

- PBKDF2-HMAC-SHA256 password hashing with per-user salts.
- Opaque authentication sessions persisted server-side.
- HttpOnly and SameSite session cookies.
- Backend permission checks on every protected route.
- No ERP secret or database password returned to the browser.
- External OAuth disabled by default in demo environments.
- Fernet-encrypted external OAuth tokens when enabled.
- Repository verification script checks for private-brand references and credential patterns.

See [`docs/security.md`](docs/security.md) for more.

## Tests

From the project root, with backend dependencies installed:

```powershell
$env:PYTHONPATH="backend"
pytest -q
python scripts\verify_portfolio.py
```

The integration tests cover:

- reconciliation formula;
- synthetic seed and dashboard;
- validation scenario;
- zone lock idempotency after reload;
- collision prevention between operators;
- recount reservation by SKU;
- divergent recount returning to Validation.

## Docker

```bash
docker build -t inventoryflow .
docker run --rm -p 10000:10000 inventoryflow
```

Or:

```bash
docker compose up --build
```

## Render

`render.yaml` is included for a one-service Docker deployment. The built Next.js frontend is copied into the FastAPI image, so the demo uses a single public URL.

For a portfolio demo, the built-in SQLite database is acceptable because the synthetic state can be recreated. For persistent hosted history, configure a PostgreSQL `DATABASE_URL` in the hosting environment.

## Project structure

```text
inventoryflow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   └── services/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
├── database/
├── docs/
├── scripts/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── render.yaml
└── README.md
```

## Design decisions

The portfolio edition intentionally removes company-specific operational adjustments. Its core reconciliation is universal: a snapshot of system stock is compared against a physical count. Domain-specific stock adjustments can be added later as independent policies without changing the counting and concurrency engines.

ERP access is abstracted behind a provider layer. The public application remains fully demonstrable without any third-party account, while the codebase still demonstrates OAuth-based integration with a real ERP.

## License

This portfolio project is provided for demonstration and educational review. Add the license that matches your intended public repository policy before publishing.
