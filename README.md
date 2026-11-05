# OLY VISION — MLOps Dashboard

A **frontend UI prototype** recreating the OLY VISION MLOps Dashboard, built with React 18 + Vite 5 + React Router 6.

> **Note:** This is a UI prototype with no backend, no authentication and no persistence. All data is mocked. Stage 2 training is a browser-side simulation (Math.random + timers), not a real ML pipeline. See the roadmap below for what needs to be built.

---

## Getting Started

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production build
```

---

## What is real vs simulated

| Feature | Status |
|---|---|
| Dashboard UI, navigation, layout | ✅ Real UI |
| Curation gallery, annotation popup, filters | ✅ Real UI |
| Admin CRUD (create/edit/delete batches) | ✅ Real UI (no persistence) |
| Training page auto-trigger at 80% threshold | ⚠️ Simulated (local timer, not connected to Curation) |
| Epoch metrics, loss/accuracy charts | ⚠️ Simulated (Math.random interpolation) |
| Training logs | ⚠️ Simulated (generated strings) |
| Deploy button | ⚠️ UI only — no handler |
| Authentication / roles | ❌ Decorative — no access control |
| Persistence | ❌ State resets on navigation/refresh |
| Real images | ❌ SVG silhouettes only |
| VLM inference / "Accept all suggestions" | ❌ Hard-coded values |
| Backend / API | ❌ Does not exist |

---

## Pages

### Dashboard
Stat cards, quick actions, recent activity table, pipeline health bars, system status.

### Curation (Gallery)
Gallery grid layout. Annotated images show ✅ overlay. Hover shows annotation tooltip. Click opens annotation popup with blurred backdrop. Requires at least one label before saving. Light/Dark mode toggle. Apple Liquid Glass theme.

### Admin Panel
Batch assignments table with progress bars. Full CRUD — create (with validation + duplicate check), edit, delete with confirmation. User management. Progress overview.

### Training (Stage 2)
Auto-trigger simulation at 80% curation. Three model cards (Gender, Age, Staff) with epoch progress bars, sparklines, live metric cards, accuracy/loss SVG charts, terminal-style scrolling logs.

---

## Project Structure

```
src/
├── components/
│   ├── Sidebar.jsx / .css
│   ├── Topbar.jsx / .css
│   └── Layout.jsx / .css
├── pages/
│   ├── Dashboard.jsx / .css
│   ├── Curation.jsx / .css
│   ├── Training.jsx / .css
│   ├── Admin.jsx / .css
│   └── NotFound.jsx
├── index.css          ← design tokens
├── App.jsx            ← HashRouter + routes + 404
└── main.jsx
```

---

## Tech Stack

| Tool | Version |
|---|---|
| React | 18.3.1 |
| Vite | 5.4.8 |
| React Router DOM | 6.26.1 |

---

## Roadmap — what needs to be built

### Before any production deployment
- [ ] Authentication and role-based access control
- [ ] Backend API (FastAPI / Node) with persistent database
- [ ] Real image storage and serving
- [ ] Replace all mocked constants with API data + loading/error states

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

Built by **Saurabh Kumar** — Stage 1 & 2 UI prototype
