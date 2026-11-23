"""
In-memory data store.
Replace with a real database (PostgreSQL / SQLite) when ready.
"""
from __future__ import annotations
import threading
from datetime import datetime
from typing import Dict, List, Optional

# ── Thread-safe ID counters ───────────────────────────────────
_batch_id_lock = threading.Lock()
_job_id_lock   = threading.Lock()
_NEXT_BATCH_ID = 7
_NEXT_JOB_NUM  = 1025


def _local_ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M')


# ── Images ───────────────────────────────────────────────────
IMAGES: List[dict] = [
    {
        'id':          i + 1,
        'label':       f'IMG_{str(i + 1).zfill(4)}',
        'location':    ['Store Entrance', 'Aisle 3', 'Checkout', 'Parking Lot', 'Lobby'][i % 5],
        'curated':     i < 5,
        'annotations': (
            [
                {'gender': 'M', 'age': '4', 'staff': 'S', 'id': 'Y'},
                {'gender': 'F', 'age': '5', 'staff': 'N', 'id': 'N'},
                {'gender': 'M', 'age': '3', 'staff': 'N', 'id': 'N'},
                {'gender': 'F', 'age': '4', 'staff': 'S', 'id': 'Y'},
                {'gender': 'M', 'age': '5', 'staff': 'N', 'id': 'N'},
            ][i] if i < 5 else None
        ),
        'timestamp': (
            f'2026-10-{str(28 - (i % 3)).zfill(2)} '
            f'{str(10 + (i % 12)).zfill(2)}:{str(i * 3 % 60).zfill(2)}'
        ),
    }
    for i in range(24)
]

# ── Batches ──────────────────────────────────────────────────
BATCHES: List[dict] = [
    {'id': 1, 'name': 'Batch-001', 'client': 'RetailCo',  'assigned': 'alice@oly.com',  'images': 500, 'pct': 100.0, 'status': 'completed'},
    {'id': 2, 'name': 'Batch-002', 'client': 'ShopMart',  'assigned': 'bob@oly.com',    'images': 480, 'pct': 72.0,  'status': 'in-progress'},
    {'id': 3, 'name': 'Batch-003', 'client': 'FreshMart', 'assigned': 'carol@oly.com',  'images': 320, 'pct': 45.0,  'status': 'in-progress'},
    {'id': 4, 'name': 'Batch-004', 'client': 'RetailCo',  'assigned': 'dave@oly.com',   'images': 600, 'pct': 10.0,  'status': 'in-progress'},
    {'id': 5, 'name': 'Batch-005', 'client': 'MegaStore', 'assigned': None,             'images': 400, 'pct': 0.0,   'status': 'unassigned'},
    {'id': 6, 'name': 'Batch-006', 'client': 'FreshMart', 'assigned': 'eve@oly.com',    'images': 550, 'pct': 88.0,  'status': 'in-progress'},
]


def next_batch_id() -> int:
    """Thread-safe batch ID generator."""
    global _NEXT_BATCH_ID
    with _batch_id_lock:
        nid = _NEXT_BATCH_ID
        _NEXT_BATCH_ID += 1
    return nid


# ── Training Jobs ─────────────────────────────────────────────
JOBS: List[dict] = [
    {'id': 'JOB-1024', 'model': 'gender', 'task': 'Gender Classification', 'status': 'completed', 'started': '2026-10-28 09:14', 'duration': '4m 32s', 'accuracy': '92.4%', 'metrics': [], 'logs': [], 'epoch': 20, 'threshold_met': True,  'final_accuracy': 92.4},
    {'id': 'JOB-1022', 'model': 'staff',  'task': 'Staff Detection',       'status': 'completed', 'started': '2026-10-27 18:02', 'duration': '6m 11s', 'accuracy': '95.1%', 'metrics': [], 'logs': [], 'epoch': 20, 'threshold_met': True,  'final_accuracy': 95.1},
    {'id': 'JOB-1021', 'model': 'gender', 'task': 'Gender Classification',  'status': 'failed',   'started': '2026-10-27 14:30', 'duration': '1m 03s', 'accuracy': '—',     'metrics': [], 'logs': [], 'epoch': 3,  'threshold_met': False, 'final_accuracy': None},
    {'id': 'JOB-1020', 'model': 'age',    'task': 'Age Classification',     'status': 'completed', 'started': '2026-10-26 11:00', 'duration': '5m 48s', 'accuracy': '86.9%', 'metrics': [], 'logs': [], 'epoch': 20, 'threshold_met': True,  'final_accuracy': 86.9},
]

# Tracks the currently running job id per model (None if idle)
RUNNING_JOBS: Dict[str, Optional[str]] = {'gender': None, 'age': None, 'staff': None}
_running_jobs_lock = threading.Lock()


def next_job_id() -> str:
    """Thread-safe job ID generator."""
    global _NEXT_JOB_NUM
    with _job_id_lock:
        jid = f'JOB-{_NEXT_JOB_NUM}'
        _NEXT_JOB_NUM += 1
    return jid


def get_job(job_id: str) -> Optional[dict]:
    return next((j for j in JOBS if j['id'] == job_id), None)
