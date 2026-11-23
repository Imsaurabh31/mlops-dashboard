"""Training job endpoints — includes SSE stream for real-time metrics."""
from __future__ import annotations
import asyncio
import json
import time
from typing import List, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import TrainingJobOut, TrainingJobDetail, TriggerTrainingRequest
from app.services import store
from app.services.training_service import start_training

router = APIRouter(prefix='/training', tags=['Training'])

TERMINAL_STATUSES = {'completed', 'failed', 'cancelled'}


def _job_to_out(j: dict) -> TrainingJobOut:
    return TrainingJobOut(
        id=j['id'], model=j['model'], task=j['task'],
        status=j['status'], started=j['started'],
        duration=j['duration'], accuracy=j['accuracy'],
        epoch=j.get('epoch', 0),
        threshold_met=j.get('threshold_met', False),
        final_accuracy=j.get('final_accuracy'),
        triggered_by=j.get('triggered_by'),
    )


@router.get('/status')
def training_status():
    """Quick overview of which models are currently training."""
    return {
        model_id: {'running': job_id is not None, 'job_id': job_id}
        for model_id, job_id in store.RUNNING_JOBS.items()
    }


@router.get('/jobs', response_model=List[TrainingJobOut])
def list_jobs():
    return [_job_to_out(j) for j in store.JOBS]


@router.get('/jobs/{job_id}/stream')
async def stream_job(job_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time training metrics.

    Frontend connects once and receives a stream of events:
      event: metric  → one epoch's metrics
      event: log     → one log line
      event: status  → job status update (running / completed / failed)
      event: done    → training finished, connection closes

    No polling needed — data pushes to the client as it is produced.
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')

    async def event_generator() -> AsyncGenerator[str, None]:
        sent_metrics = 0
        sent_logs    = 0

        # Send initial state immediately
        yield _sse('status', {
            'job_id': job_id,
            'status': job['status'],
            'epoch':  job.get('epoch', 0),
        })

        while True:
            await asyncio.sleep(0.3)   # check every 300 ms

            current_job = store.get_job(job_id)
            if not current_job:
                yield _sse('done', {'job_id': job_id, 'reason': 'job_not_found'})
                break

            # Stream new metrics
            metrics = current_job.get('metrics', [])
            for m in metrics[sent_metrics:]:
                yield _sse('metric', m)
                sent_metrics += 1

            # Stream new logs
            logs = current_job.get('logs', [])
            for line in logs[sent_logs:]:
                yield _sse('log', {'line': line})
                sent_logs += 1

            # Send status update if epoch changed
            yield _sse('status', {
                'job_id':         job_id,
                'status':         current_job['status'],
                'epoch':          current_job.get('epoch', 0),
                'threshold_met':  current_job.get('threshold_met', False),
                'final_accuracy': current_job.get('final_accuracy'),
                'accuracy':       current_job['accuracy'],
                'duration':       current_job['duration'],
            })

            # Close stream when job reaches terminal state
            if current_job['status'] in TERMINAL_STATUSES:
                yield _sse('done', {
                    'job_id':        job_id,
                    'status':        current_job['status'],
                    'final_accuracy': current_job.get('final_accuracy'),
                    'threshold_met': current_job.get('threshold_met', False),
                    'duration':      current_job['duration'],
                })
                break

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control':               'no-cache',
            'X-Accel-Buffering':           'no',
            'Access-Control-Allow-Origin': '*',
        },
    )


def _sse(event: str, data: dict) -> str:
    """Format a single SSE message."""
    return f'event: {event}\ndata: {json.dumps(data)}\n\n'


@router.get('/jobs/{job_id}/logs')
def get_job_logs(job_id: str):
    """REST fallback — returns all logs + metrics at once (for non-SSE clients)."""
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
    seen, started = set(), []
    for model_id in body.model_ids:
        if model_id in seen:
            continue
        seen.add(model_id)
        job = start_training(model_id, triggered_by_batch=body.batch_id)
        started.append({'id': job['id'], 'model': job['model'], 'status': job['status']})
    return {'jobs': started}
