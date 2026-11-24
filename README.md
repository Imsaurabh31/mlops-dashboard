# OLY VISION — MLOps Dashboard

> **Stage 1, 2 & 3** — React frontend + FastAPI backend
> Built by **Saurabh Kumar**

---

## Quick Start

### Frontend (React + Vite)
```bash
# Run from repo root
npm install
npm run dev      # → http://localhost:5173
npm run build    # production build
npm run lint     # lint check
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

---

## What is real vs simulated

| Feature | Status |
|---|---|
| Dashboard UI, navigation, layout | ✅ Real UI |
| Curation gallery — gallery view, annotation popup, filters | ✅ Real UI |
| Curation — Apple Liquid Glass theme, dark/light mode | ✅ Real UI |
| Admin CRUD — create, edit, delete batches | ✅ Real UI + backend API |
| Admin modals — focus trap, Escape, role=dialog | ✅ Accessible |
| Dashboard stats — images, curated, pending | ✅ Live from backend API |
| Backend REST API (FastAPI) | ✅ Running |
| Batch completion → auto-training trigger | ✅ Working |
| SSE real-time training metrics | ✅ Live stream — no polling |
| Annotation quality score | ✅ Backend API working |
| Pluggable training scripts | ✅ Swap scripts without changing pipeline |
| **Model auto-deployment** | ✅ **Stage 3 — working** |
| **Deployment registry** | ✅ **Active deployments per model** |
| **Rollback to previous version** | ✅ **One click rollback** |
| **Health monitoring** | ✅ **Latency, uptime, requests/hr** |
| **Deployment audit log** | ✅ **Every action recorded** |
| Training page auto-trigger at 80% | ⚠️ Frontend simulation only |
| Epoch metrics, charts | ⚠️ Mock data until real scripts arrive |
| Authentication / roles | ❌ Not implemented yet |
| Persistence | ❌ In-memory — needs database |
| Real images | ❌ SVG silhouettes only |
| VLM inference | ❌ Hard-coded placeholder |

---

## Pages

### Dashboard
Live stat cards (from API), quick actions, recent activity, pipeline health bars, system status, storage donut.

### Curation
Gallery grid with Apple Liquid Glass theme. Annotated images show ✅ overlay. Hover shows annotation tooltip. Click opens focused popup with blur backdrop. Keyboard shortcuts. Light/Dark mode. Annotation quality flagging.

### Admin Panel
Batch assignments with progress bars. Full CRUD connected to backend. Accessible modals (focus trap, Escape, `role="dialog"`). User management. Progress overview with live derived stats.

### Training
Auto-trigger at 80% curation. Model cards (Gender, Age, Staff). **SSE real-time panel** with live accuracy/loss charts, epoch progress, terminal logs. Pluggable training scripts.

### Deployment *(Stage 3)*
Active deployment cards per model with health indicators. Deploy trained models, rollback to previous versions, stop endpoints. Deployment version history. Audit log of all actions.

---

## Backend API

Base URL: `http://localhost:8000/api`

### Images
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/images/stats/summary` | Live curated/pending counts |
| GET | `/images/` | List images (filter by curated) |
| GET | `/images/{id}` | Get single image |
| POST | `/images/{id}/annotate` | Save annotation |

### Batches
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/batches/` | List all batches |
| POST | `/batches/` | Create batch |
| PATCH | `/batches/{id}` | Update batch |
| DELETE | `/batches/{id}` | Delete batch |
| **POST** | **`/batches/{id}/complete`** | **Mark complete → auto-trigger training** |

### Training
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/training/jobs` | List all jobs |
| GET | `/training/jobs/{id}` | Job details |
| GET | `/training/jobs/{id}/logs` | Logs + metrics (REST) |
| **GET** | **`/training/jobs/{id}/stream`** | **SSE real-time stream** |
| GET | `/training/status` | Running model status |
| POST | `/training/trigger` | Manual trigger |

### Quality
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/quality/scores` | Quality score per image (0–100) |
| GET | `/quality/flagged` | Images flagged for re-review |
| GET | `/quality/summary` | Overall quality stats |
| POST | `/quality/{id}/approve` | Approve flagged image |
| POST | `/quality/{id}/flag` | Manually flag image |

### Deployment *(Stage 3)*
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/deploy/` | List all deployments |
| GET | `/deploy/active` | Active deployment per model |
| GET | `/deploy/summary` | Health overview stats |
| GET | `/deploy/log` | Deployment audit log |
| GET | `/deploy/{id}` | Single deployment detail |
| **POST** | **`/deploy/{job_id}/deploy`** | **Deploy a trained model** |
| **POST** | **`/deploy/{dep_id}/rollback`** | **Rollback to previous version** |
| POST | `/deploy/{dep_id}/stop` | Stop a deployment (requires confirm) |
| POST | `/deploy/health/refresh` | Refresh health checks |

---

## Project Structure

```
mlops-dashboard/              ← repo root (frontend lives here)
├── src/
│   ├── api/
│   │   ├── client.js         ← typed API client for all endpoints
│   │   └── useApi.js         ← useApiData, usePolling, useSSEJob hooks
│   ├── components/
│   │   ├── Sidebar.jsx/css   ← dark nav sidebar
│   │   ├── Topbar.jsx/css    ← breadcrumbs, search, user
│   │   ├── Layout.jsx/css    ← sidebar + topbar wrapper
│   │   ├── Modal.jsx/css     ← accessible modal (focus trap, Escape)
│   │   └── SSELivePanel.jsx/css ← real-time training panel (SSE)
│   ├── pages/
│   │   ├── Dashboard.jsx/css
│   │   ├── Curation.jsx/css
│   │   ├── Training.jsx/css
│   │   ├── Admin.jsx/css
│   │   ├── Deployment.jsx/css ← Stage 3
│   │   └── NotFound.jsx
│   ├── index.css             ← design tokens (CSS variables)
│   ├── App.jsx               ← HashRouter + routes + 404
│   └── main.jsx
├── backend/
│   ├── app/
│   │   ├── main.py                    ← FastAPI app + CORS
│   │   ├── models/
│   │   │   └── schemas.py             ← Pydantic models
│   │   ├── routers/
│   │   │   ├── images.py
│   │   │   ├── batches.py             ← CRUD + completion trigger
│   │   │   ├── training.py            ← jobs, SSE stream, trigger
│   │   │   ├── quality.py             ← annotation quality scoring
│   │   │   └── deployment.py          ← Stage 3 deployment endpoints
│   │   └── services/
│   │       ├── store.py               ← in-memory store
│   │       ├── script_runner.py       ← pluggable script runner
│   │       ├── training_service.py    ← job management + trigger
│   │       ├── deployment_store.py    ← deployment registry
│   │       └── deployment_service.py  ← auto-deploy, rollback, health
│   ├── scripts/
│   │   └── dummy_training.py          ← swap for real training scripts
│   ├── verify.py                      ← 18-test suite (Stages 1 & 2)
│   ├── verify_stage3.py               ← 11-test suite (Stage 3)
│   └── requirements.txt
├── package.json
├── vite.config.js
└── .env                      ← VITE_API_URL=http://localhost:8000/api
```

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| React | 18.3.1 | Frontend UI |
| Vite | 5.4.8 | Build tool |
| React Router DOM | 6.26.1 | Client-side routing |
| oxlint | 0.4.0 | Linting |
| FastAPI | 0.115.4 | Backend API |
| Uvicorn | 0.32.0 | ASGI server |
| Pydantic | 2.9.2 | Data validation |

---

## Swapping Training Scripts

The pipeline is fully pluggable. To use real training scripts:

1. Write a script that prints to stdout:
```
LOG   <message>
METRIC <epoch> <train_acc> <val_acc> <train_loss> <val_loss>
DONE  <final_val_acc>
```
2. Update `MODEL_SCRIPTS` in `backend/app/services/script_runner.py`
3. Nothing else changes — pipeline reads stdout automatically

---

## Roadmap

### Stage 3 — Model Auto Deployment ✅ Complete
- [x] Deployment pipeline triggered by accuracy threshold
- [x] Endpoint registry with health monitoring
- [x] Rollback to previous version
- [x] Deployment audit log
- [x] Deploy / Rollback / Stop endpoints

### Stage 4 — MLOps Dashboard v2
- [ ] Authentication and RBAC
- [ ] Persistent database (PostgreSQL)
- [ ] Real image storage
- [ ] Real training scripts integration
- [ ] WebSocket metrics from actual job runner
- [ ] Model registry (artefacts, lineage)
- [ ] Data protection (DPDP Act 2023 / GDPR)
