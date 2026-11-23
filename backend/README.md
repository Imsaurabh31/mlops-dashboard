# OLY VISION — MLOps Backend

FastAPI backend for the OLY VISION MLOps Dashboard.

---

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## Key Endpoints

### Batches
| Method | Path | Description |
|--------|------|-------------|
| GET    | `/api/batches/` | List all batches |
| POST   | `/api/batches/` | Create a new batch |
| PATCH  | `/api/batches/{id}` | Update a batch |
| DELETE | `/api/batches/{id}` | Delete a batch |
| **POST** | **`/api/batches/{id}/complete`** | **Mark batch complete → auto-triggers training** |

### Training
| Method | Path | Description |
|--------|------|-------------|
| GET    | `/api/training/jobs` | List all training jobs |
| GET    | `/api/training/jobs/{id}` | Get job details + metrics |
| GET    | `/api/training/jobs/{id}/logs` | Get live/historical logs |
| POST   | `/api/training/trigger` | Manually trigger training |
| GET    | `/api/training/status` | Check which models are running |

### Images
| Method | Path | Description |
|--------|------|-------------|
| GET    | `/api/images/` | List images (filter by curated=true/false) |
| GET    | `/api/images/{id}` | Get single image |
| POST   | `/api/images/{id}/annotate` | Save annotation |
| GET    | `/api/images/stats/summary` | Curated/pending counts |

---

## Auto-Training Trigger Flow

```
Curator annotates all images in a batch
        ↓
POST /api/batches/{batch_id}/complete
        ↓
Batch marked pct=100, status=completed
        ↓
trigger_on_batch_completion(batch_id) called
        ↓
Training starts for gender + age + staff models
(each in a separate daemon thread)
        ↓
GET /api/training/jobs/{id}/logs  ← poll from frontend for live updates
```

---

## Replacing Mock Training

The `scripts/mock_training.py` file is a placeholder.
When Thiyagu shares the real training scripts:

1. Replace `_run_training_script()` in `app/services/training_service.py`
2. Use `subprocess.Popen()` to run the real script
3. Parse stdout lines matching `METRIC epoch train_acc val_acc train_loss val_loss`
4. Stream parsed metrics into `job['metrics']` and `job['logs']`

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              ← FastAPI app + CORS + routers
│   ├── models/
│   │   └── schemas.py       ← Pydantic request/response models
│   ├── routers/
│   │   ├── batches.py       ← Batch CRUD + completion trigger
│   │   ├── training.py      ← Training job endpoints
│   │   └── images.py        ← Image annotation endpoints
│   └── services/
│       ├── store.py         ← In-memory data (replace with DB)
│       └── training_service.py  ← Background training + trigger logic
├── scripts/
│   └── mock_training.py     ← Placeholder training script
└── requirements.txt
```
