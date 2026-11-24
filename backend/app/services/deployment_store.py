"""
Deployment store — tracks all deployed model versions.
Replace with a real database when ready.
"""
from __future__ import annotations
import threading
from datetime import datetime
from typing import Dict, List, Optional

_lock          = threading.Lock()
_NEXT_DEPLOY   = 1


def _ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M')


# ── Deployment registry ──────────────────────────────────────
# Each entry represents one deployed version of a model.
DEPLOYMENTS: List[dict] = [
    {
        'id':            'DEP-001',
        'model':         'gender',
        'task':          'Gender Classification',
        'version':       'v1',
        'job_id':        'JOB-1024',
        'accuracy':      92.4,
        'status':        'active',
        'endpoint':      '/api/infer/gender',
        'deployed_at':   '2026-10-28 10:00',
        'deployed_by':   'admin',
        'latency_ms':    18,
        'requests_hr':   1200,
        'uptime_pct':    99.8,
        'health':        'healthy',
        'last_checked':  '2026-10-28 11:00',
        'rollback_to':   None,
    },
    {
        'id':            'DEP-002',
        'model':         'staff',
        'task':          'Staff Detection',
        'version':       'v1',
        'job_id':        'JOB-1022',
        'accuracy':      95.1,
        'status':        'active',
        'endpoint':      '/api/infer/staff',
        'deployed_at':   '2026-10-27 19:00',
        'deployed_by':   'admin',
        'latency_ms':    22,
        'requests_hr':   1200,
        'uptime_pct':    99.9,
        'health':        'healthy',
        'last_checked':  '2026-10-28 11:00',
        'rollback_to':   None,
    },
    {
        'id':            'DEP-003',
        'model':         'age',
        'task':          'Age Classification',
        'version':       'v1',
        'job_id':        'JOB-1020',
        'accuracy':      86.9,
        'status':        'active',
        'endpoint':      '/api/infer/age',
        'deployed_at':   '2026-10-26 12:00',
        'deployed_by':   'admin',
        'latency_ms':    25,
        'requests_hr':   1200,
        'uptime_pct':    99.5,
        'health':        'healthy',
        'last_checked':  '2026-10-28 11:00',
        'rollback_to':   None,
    },
]

# Tracks the currently active deployment per model
ACTIVE: Dict[str, Optional[str]] = {
    'gender': 'DEP-001',
    'age':    'DEP-003',
    'staff':  'DEP-002',
}

# Deployment log entries
DEPLOY_LOG: List[dict] = []


def next_deploy_id() -> str:
    global _NEXT_DEPLOY
    with _lock:
        did = f'DEP-{_NEXT_DEPLOY:03d}'
        _NEXT_DEPLOY += 1
    return did


def get_deployment(dep_id: str) -> Optional[dict]:
    return next((d for d in DEPLOYMENTS if d['id'] == dep_id), None)


def get_active(model: str) -> Optional[dict]:
    dep_id = ACTIVE.get(model)
    return get_deployment(dep_id) if dep_id else None


def add_log(action: str, model: str, detail: str, actor: str = 'system') -> None:
    DEPLOY_LOG.append({
        'timestamp': _ts(),
        'action':    action,
        'model':     model,
        'detail':    detail,
        'actor':     actor,
    })
