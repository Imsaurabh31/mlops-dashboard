"""
Training service — public API for starting and triggering training jobs.

The actual training is delegated to script_runner.py which runs any
script that follows the standard stdout interface. To swap scripts,
update MODEL_SCRIPTS in script_runner.py — nothing here changes.
"""
from __future__ import annotations
import threading
from datetime import datetime
from typing import Optional

from app.services import store
from app.services.script_runner import MODEL_CONFIG, run_script


def _local_ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def start_training(model_id: str, triggered_by_batch: Optional[int] = None) -> dict:
    """
    Start a training job for model_id.
    Returns the new job dict immediately (status='running').
    Thread-safe: uses a lock to prevent duplicate concurrent starts.
    The actual training runs in a background daemon thread via script_runner.
    """
    if model_id not in MODEL_CONFIG:
        raise ValueError(
            f'Unknown model: {model_id!r}. '
            f'Available: {list(MODEL_CONFIG)}'
        )

    # Thread-safe guard — check and set atomically
    with store._running_jobs_lock:
        if store.RUNNING_JOBS.get(model_id):
            existing_id = store.RUNNING_JOBS[model_id]
            existing    = store.get_job(existing_id)
            return existing or {'id': existing_id, 'status': 'running'}

        job_id = store.next_job_id()
        store.RUNNING_JOBS[model_id] = job_id

    cfg = MODEL_CONFIG[model_id]

    triggered_label = (
        f'Batch-{triggered_by_batch:03d}'
        if triggered_by_batch is not None
        else 'manual'
    )

    job: dict = {
        'id':             job_id,
        'model':          model_id,
        'task':           cfg['task'],
        'status':         'running',
        'started':        _local_ts(),
        'duration':       '—',
        'accuracy':       '—',
        'metrics':        [],
        'logs':           [],
        'epoch':          0,
        'triggered_by':   triggered_label,
        'threshold_met':  False,
        'final_accuracy': None,
    }

    store.JOBS.insert(0, job)

    # Delegate to script_runner — this is the only place that matters
    # when swapping training scripts
    thread = threading.Thread(
        target=run_script,
        args=(model_id, job_id),
        daemon=True,
        name=f'train-{model_id}-{job_id}',
    )
    thread.start()
    return job


def trigger_on_batch_completion(batch_id: int) -> list[dict]:
    """
    Called when a batch's curation is marked 100% complete.
    Triggers training for all three models (skips any already running).
    """
    return [
        start_training(model_id, triggered_by_batch=batch_id)
        for model_id in ['gender', 'age', 'staff']
    ]
