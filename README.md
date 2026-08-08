# AI-Powered Endpoint Assurance Validation

A production-shaped full-stack platform that validates endpoint security controls —
**Antivirus, EDR, Firewall, and BitLocker** — against a configurable assurance
blueprint, classifies findings by severity, scores compliance, and explains
**why** each finding matters and **what to do** about it.

The validation core is **deterministic** (a SQLite lookup + a rules engine — it
never hallucinates). An LLM is layered on top purely to phrase the
explanations.

```
React + Vite + TypeScript + Tailwind (SPA)  ──►  FastAPI + SQLAlchemy + Pydantic  ──►  SQLite
                                                   │
                                                   ├─ deterministic validation engine (4 pluggable control validators)
                                                   ├─ ReportLab (PDF) + OpenPyXL (Excel) reports
                                                   └─ LLM + Chroma RAG 
```

---
## Features (6 modules)

| Module | What it does |
|---|---|
| **Login** | JWT auth against a seeded `users` table (bcrypt-hashed passwords). |
| **Dashboard** | Fleet KPIs, compliance trend, findings-by-severity donut, per-control compliance, top findings. |
| **Endpoints** | Searchable / filterable / sortable / paginated table with per-control status and score. |
| **Endpoint Detail** | Asset info, four control cards (PASS / WARNING / FAIL / NO_DATA), evidence, findings, AI recommendations, per-endpoint PDF. |
| **Blueprint** | The assurance baseline made visible — every rule grouped by control, with severity, your policy reference, the CIS safeguard mapping, the firewall/BitLocker golden images, and the internal AV/EDR policies. |
| **AI Assistant** | per-endpoint checks, fleet metrics ("how many fail BitLocker?"), lists ("which endpoints are failing?"), policy/blueprint lookups, and "what/why" explanations — always grounded in the DB / rules / policies, and **every answer cites its sources**. |
| **Reports** | Fleet executive-summary PDF and a detailed findings Excel workbook. |

Each control returns **PASS / WARNING / FAIL / NO_DATA**; findings are classified
**critical / high / medium / low**; endpoints and the fleet get a 0–100 compliance score.

### Named platform components
- **AI Assurance Agent** — automation & evidence collection (ETL); status surfaced at `/api/v1/system/collection` and the dashboard's *Data Collection* card.
### How the AI stays grounded
Facts always come from deterministic queries (DB + rules engine); the local LLM generates
explanations, strictly over retrieved policy/CIS excerpts. Every
chat answer carries a `sources` list. 
---
## Architecture

```
backend/
  app/
    main.py               FastAPI app factory (CORS, logging, routers, /health)
    config.py             env-driven settings (pydantic-settings)
    database.py           SQLAlchemy engine + session
    core/                 security (JWT/bcrypt), auth deps, logging
    db_models/            ORM: user, asset, av/edr/firewall/bitlocker controls, blueprint_rule 
    schemas/              Pydantic API contracts
    repositories/         data access (repository pattern) + time normalization
    validators/           pluggable per-control validators (base + 4 controls + registry)
    services/             validation, compliance/scoring, AI, reports
    api/v1/               auth, dashboard, endpoints, chat, reports routers
    llm/  rag/            AI client + Chroma retriever 
  data/
    endpoint_security.db  SQLite database used by the default configuration
  chroma_store/           Persistent ChromaDB data
  policies/
    master_policies/      Internal policy documents
    standards/            CIS and other standard documents
  scripts/                init_db, import_data (ETL), seed_blueprint, seed_users
  tests/                  pytest: validators, scoring, auth, API (22 tests)
frontend/
  src/
    lib/                  axios client (JWT interceptor), typed API, constants, query client
    store/                auth + theme
    components/           reusable UI (shadcn-style primitives + StatusBadge, KpiCard, ...)
    features/             auth, dashboard, endpoints, chat, reports pages
```

**Design principles:** SOLID / DRY / KISS, clean layering (API → services →
repositories → ORM), repository pattern, a pluggable validator registry (adding a
5th control = subclass + register), and a single canonical blueprint baseline
(`app/services/blueprint_defaults.py`).

### Data model & the positional re-key

Assets, AV, and EDR evidence are keyed by CORP hostnames (`CORP-SRV-###`,
`CORP-WKSTN-###`). 

### Evaluation reference time

The seed dataset is a frozen point-in-time snapshot. Time-based freshness rules
(EDR check-in ≤ 24h, AV signature age ≤ 7d) are therefore evaluated against the
dataset's **most recent evidence timestamp** by default, not the wall clock — so
results stay realistic and stable no matter when you run the demo. Set
`EVAL_REFERENCE_TIME=now` once live evidence is flowing. See `app/config.py`.

---
## Quick start

### 1. Backend (Python 3.11+)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate       Linux/macOS:  source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
python scripts/init_db.py --drop      # create schema from the ORM models
python scripts/seed_blueprint.py      # 21 blueprint rules across the 4 controls
python scripts/seed_users.py          # seed the admin account
python scripts/import_data.py         # ETL: load all evidence (with positional re-key)

python -m uvicorn app.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs> · Health: <http://localhost:8000/health>

### 2. Frontend (Node 18+)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxies /api and /health to :8000)
```

Open <http://localhost:5173> and sign in with **`admin` / `admin123`**
(configurable via `DEFAULT_ADMIN_*` in `backend/.env`; change before production).

### 3. the AI narrative layer (currently not needed since we now use gemini API not local)

```bash
ollama pull smollm2:360m       # intent extraction
ollama pull smollm2:1.7b       # recommendations
ollama pull nomic-embed-text   # RAG embeddings
pip install chromadb           # optional: enables policy/CIS RAG retrieval
python -c "from app.rag.retriever import ingest_policies; \
  ingest_policies('policies/standards','standards'); \
  ingest_policies('policies/master_policies','master_policies')"
```

Model names / host are configurable in `backend/.env` (`OLLAMA_HOST`,
`EXTRACTION_MODEL`, `RECOMMENDATION_MODEL`, `AI_ENABLED`).

---
## Testing

```bash
cd backend && python -m pytest        # 22 tests: validators, scoring, auth, API
cd frontend && npm run build          # type-check (tsc) + production build
```

---
## API surface (`/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | OAuth2 password flow → JWT |
| GET  | `/auth/me` | current user |
| GET  | `/dashboard/summary` | fleet KPIs & aggregates |
| GET  | `/endpoints` | list (search / filter / sort / paginate) |
| GET  | `/endpoints/{hostname}` | full detail + validation + recommendations |
| GET  | `/endpoints/{hostname}/recommendations` | AI recommendations |
| POST | `/chat` | grounded NL query engine (endpoint / fleet-metric / list / policy / explanation) with sources |
| GET  | `/chat/status` | LLM online/offline indicator |
| GET  | `/endpoints/{hostname}/recommendations` | on-demand LLM narrative summary |
| GET  | `/blueprint` | the assurance baseline: rules + CIS + policy refs + golden images |
| GET  | `/system/collection` · `/system/components` | assurance-agent collection status & component health |
| GET  | `/reports/fleet.pdf` · `/reports/findings.xlsx` · `/reports/endpoint/{hostname}.pdf` | reports |

All data routes require a bearer token.

---
## Configuration

All tunables live in `backend/app/config.py` and can be overridden via
`backend/.env` (copy from `backend/.env.example`). Key settings: `DATABASE_URL`,
`SECRET_KEY` (**change in production**), `CORS_ORIGINS`, `AI_ENABLED`,
`OLLAMA_HOST`, `EVAL_REFERENCE_TIME`, `POLICIES_ROOT`, and `CHROMA_PATH`.
By default, the SQLite database is stored at `backend/data/endpoint_security.db`,
policy documents at `backend/policies/`, and the persistent ChromaDB store at
`backend/chroma_store/`. The database is portable — point
`DATABASE_URL` at PostgreSQL or SQL Server and re-run the scripts.
