"""Training job endpoints."""
from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException

from app.models.schemas import TrainingJobOut, TrainingJobDetail, TriggerTrainingRequest
from app.services import store
from app.services.training_service import start_training

router = APIRouter(prefix='/training', tags=['Training'])


def _job_to_out(j: dict) -> TrainingJobOut:
    return TrainingJobOut(
        id=j['id'],
        model=j['model'],
        task=j['task'],
        status=j['status'],
        started=j['started'],
        duration=j['duration'],
        accuracy=j['accuracy'],
        epoch=j.get('epoch', 0),
        threshold_met=j.get('threshold_met', False),
        final_accuracy=j.get('final_accuracy'),
        triggered_by=j.get('triggered_by'),
    )


@router.get('/status')
def training_status():
    """Quick overview of which models are currently training."""
    return {
        model_id: {
            'running': job_id is not None,
            'job_id':  job_id,
        }
        for model_id, job_id in store.RUNNING_JOBS.items()
    }


@router.get('/jobs', response_model=List[TrainingJobOut])
def list_jobs():
    return [_job_to_out(j) for j in store.JOBS]


@router.get('/jobs/{job_id}/logs')
def get_job_logs(job_id: str):
    """Return live logs + metrics for a job. Poll this endpoint for real-time updates."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return {
        'job_id':         job_id,
        'status':         job['status'],
        'epoch':          job.get('epoch', 0),
        'threshold_met':  job.get('threshold_met', False),
        'final_accuracy': job.get('final_accuracy'),
        'metrics':        job.get('metrics', []),
        'logs':           job.get('logs', []),
    }


@router.get('/jobs/{job_id}', response_model=TrainingJobDetail)
def get_job(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return TrainingJobDetail(
        id=job['id'], model=job['model'], task=job['task'],
        status=job['status'], started=job['started'],
        duration=job['duration'], accuracy=job['accuracy'],
        epoch=job.get('epoch', 0),
        threshold_met=job.get('threshold_met', False),
        final_accuracy=job.get('final_accuracy'),
        triggered_by=job.get('triggered_by'),
        metrics=job.get('metrics', []),
        logs=job.get('logs', []),
    )


@router.post('/trigger')
def trigger_training(body: TriggerTrainingRequest):
    """Manually trigger training for specified models."""
    # Deduplicate model_ids to avoid double-triggering
    seen = set()
    started = []
    for model_id in body.model_ids:
        if model_id in seen:
            continue
        seen.add(model_id)
        job = start_training(model_id, triggered_by_batch=body.batch_id)
        started.append({'id': job['id'], 'model': job['model'], 'status': job['status']})
    return {'jobs': started}
