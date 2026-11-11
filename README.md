# OLY VISION — MLOps Dashboard

A **frontend UI prototype + FastAPI backend** for the OLY VISION MLOps Dashboard.

> **Note:** Stage 1 & 2 frontend is a UI prototype. Stage 2 training uses a mock simulation until real training scripts are provided. See the roadmap below for what still needs to be built.

---

## Getting Started

### Frontend
```bash
cd mlops-dashboard
npm install
npm run dev        # http://localhost:5173
npm run build      # production build
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## What is real vs simulated

| Feature | Status |
|---|---|
| Dashboard UI, navigation, layout | ✅ Real UI |
| Curation gallery, annotation popup, filters | ✅ Real UI |
| Admin CRUD (create/edit/delete batches) | ✅ Real UI + connected to backend API |
| Dashboard stats (images, curated, pending) | ✅ Live from backend API |
| Backend REST API (FastAPI) | ✅ Running — images, batches, training jobs |
| Batch completion → auto-training trigger | ✅ Working — triggers all 3 models on completion |
| Training job management (start, logs, status) | ✅ Backend API working |
| Training page auto-trigger at 80% threshold | ⚠️ Frontend simulation — not connected to backend yet |
| Epoch metrics, loss/accuracy charts | ⚠️ Simulated (Math.random interpolation) until real scripts arrive |
| Training logs | ⚠️ Mock logs — backend ready to stream real logs |
| Deploy button | ⚠️ UI only — Stage 3 will implement this |
| Authentication / roles | ❌ Decorative — no access control yet |
| Persistence | ❌ In-memory store — needs database |
| Real images | ❌ SVG silhouettes only |
| VLM inference / "Accept all suggestions" | ❌ Hard-coded values |

---

## Pages

### Dashboard
Stat cards (live from API), quick actions, recent activity table, pipeline health bars, system status.

### Curation (Gallery)
Gallery grid. Annotated images show ✅ overlay. Hover shows annotation tooltip. Click opens popup with blurred backdrop. Requires at least one label before saving. Light/Dark mode. Apple Liquid Glass theme.

### Admin Panel
Batch assignments table with progress bars. Full CRUD — connected to backend API. Create batch form with validation + duplicate check. User management. Progress overview.

### Training (Stage 2)
Auto-trigger simulation at 80% curation. Three model cards (Gender, Age, Staff) with epoch progress bars, sparklines, live metric cards, accuracy/loss SVG charts, terminal-style scrolling logs.

---

## Backend API

Base URL: `http://localhost:8000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/images/stats/summary` | Curated/pending counts |
| GET | `/images/` | List all images |
| POST | `/images/{id}/annotate` | Save annotation |
| GET | `/batches/` | List all batches |
| POST | `/batches/` | Create batch |
| PATCH | `/batches/{id}` | Update batch |
| DELETE | `/batches/{id}` | Delete batch |
| **POST** | **`/batches/{id}/complete`** | **Mark complete → auto-trigger training** |
| GET | `/training/jobs` | List training jobs |
| GET | `/training/jobs/{id}/logs` | Live logs + metrics |
| GET | `/training/status` | Running models status |
| POST | `/training/trigger` | Manual training trigger |

---

## Project Structure

```
MLOPS/
├── backend/                    ← FastAPI backend
│   ├── app/
│   │   ├── main.py             ← FastAPI app + CORS
│   │   ├── models/schemas.py   ← Pydantic models
│   │   ├── routers/
│   │   │   ├── images.py
│   │   │   ├── batches.py      ← Batch CRUD + completion trigger
│   │   │   └── training.py     ← Job management + live logs
│   │   └── services/
│   │       ├── store.py        ← In-memory store (replace with DB)
│   │       └── training_service.py ← Background training + trigger
│   ├── scripts/mock_training.py
│   ├── verify.py               ← 18-test verification script
│   └── requirements.txt
│
└── mlops-dashboard/            ← React + Vite frontend
    ├── src/
    │   ├── api/
    │   │   ├── client.js       ← API client for all endpoints
    │   │   └── useApi.js       ← React hooks (usePolling, useJobLogs)
    │   ├── components/
    │   │   ├── Sidebar.jsx / .css
    │   │   ├── Topbar.jsx / .css
    │   │   └── Layout.jsx / .css
    │   ├── pages/
    │   │   ├── Dashboard.jsx / .css
    │   │   ├── Curation.jsx / .css
    │   │   ├── Training.jsx / .css
    │   │   ├── Admin.jsx / .css
    │   │   └── NotFound.jsx
    │   ├── index.css           ← design tokens
    │   ├── App.jsx             ← HashRouter + routes + 404
    │   └── main.jsx
    └── .env                    ← VITE_API_URL=http://localhost:8000/api
```

---

## Tech Stack

| Tool | Version |
|---|---|
| React | 18.3.1 |
| Vite | 5.4.8 |
| React Router DOM | 6.26.1 |
| FastAPI | 0.115.4 |
| Uvicorn | 0.32.0 |
| Pydantic | 2.9.2 |

---

## Roadmap — what needs to be built

### Before any production deployment
- [ ] Authentication and role-based access control
- [ ] Replace in-memory store with persistent database (PostgreSQL / SQLite)
- [ ] Real image storage and serving
- [ ] Replace mocked training simulation with real scripts (pending from Thiyagu)

### Stage 3 — Model Auto Deployment
- [ ] Real deployment pipeline triggered by accuracy threshold
- [ ] Endpoint registry with live health monitoring
- [ ] Rollback to previous version
- [ ] Audit logs for deploy actions

### Stage 4 — MLOps Dashboard v2
- [ ] Real curated count driving the auto-training trigger
- [ ] WebSocket / SSE for live training metrics from actual job runner
- [ ] Model registry (artefacts, dataset version, lineage)
- [ ] Data protection approach for CCTV frames (DPDP Act 2023 / GDPR)

---

Built by **Saurabh Kumar** — Stage 1 & 2 (UI prototype + FastAPI backend)
