"""
Stage 3 — Model Auto Deployment endpoints.

Endpoints:
  GET  /api/deploy/                    — list all deployments
  GET  /api/deploy/active              — currently active deployments per model
  GET  /api/deploy/{dep_id}            — single deployment detail
  POST /api/deploy/{job_id}/deploy     — manually deploy a trained model
  POST /api/deploy/{dep_id}/rollback   — rollback to previous version
  POST /api/deploy/{dep_id}/stop       — stop a deployment (with confirm)
  POST /api/deploy/health/refresh      — refresh health checks
  GET  /api/deploy/log                 — deployment audit log
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import deployment_store as ds
from app.services import deployment_service as svc
from app.services import store as job_store

router = APIRouter(prefix='/deploy', tags=['Deployment'])


# ── Request schemas ──────────────────────────────────────────
class DeployRequest(BaseModel):
    actor: str = 'admin'


class StopRequest(BaseModel):
    confirm: bool = False
    actor:   str  = 'admin'


# ── Helpers ──────────────────────────────────────────────────
def _dep_out(d: dict) -> dict:
    """Safe copy without internal references."""
    return {k: v for k, v in d.items()}


# ── Endpoints ────────────────────────────────────────────────

@router.get('/')
def list_deployments(status: Optional[str] = None):
    """List all deployments. Filter by status: active | archived | stopped."""
    deps = ds.DEPLOYMENTS
    if status:
        deps = [d for d in deps if d['status'] == status]
    return [_dep_out(d) for d in deps]


@router.get('/active')
def active_deployments():
    """Currently active deployment for each model."""
    result = {}
    for model in ['gender', 'age', 'staff']:
        dep = ds.get_active(model)
        result[model] = _dep_out(dep) if dep else None
    return result


@router.get('/log')
def deployment_log():
    """Audit log of all deployment actions."""
    return ds.DEPLOY_LOG[::-1]   # newest first


@router.post('/health/refresh')
def refresh_health():
    """Simulate health check refresh for all active deployments."""
    svc.refresh_health()
    return {'message': 'Health refreshed', 'checked': sum(1 for d in ds.DEPLOYMENTS if d['status'] == 'active')}


@router.get('/summary')
def deployment_summary():
    """Overview stats for the deployment dashboard."""
    active   = [d for d in ds.DEPLOYMENTS if d['status'] == 'active']
    archived = [d for d in ds.DEPLOYMENTS if d['status'] == 'archived']
    stopped  = [d for d in ds.DEPLOYMENTS if d['status'] == 'stopped']
    degraded = [d for d in active if d['health'] == 'degraded']

    return {
        'total_active':   len(active),
        'total_archived': len(archived),
        'total_stopped':  len(stopped),
        'degraded':       len(degraded),
        'models_deployed': list({d['model'] for d in active}),
        'avg_latency_ms': round(sum(d['latency_ms'] for d in active) / len(active), 1) if active else 0,
        'avg_uptime_pct': round(sum(d['uptime_pct'] for d in active) / len(active), 2) if active else 0,
    }


@router.get('/{dep_id}')
def get_deployment(dep_id: str):
    dep = ds.get_deployment(dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail='Deployment not found')
    return _dep_out(dep)


@router.post('/{job_id}/deploy')
def deploy_model(job_id: str, body: DeployRequest):
    """
    Manually deploy a trained model from a completed job.
    The job must have status=completed and threshold_met=True.
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f'Job {job_id} not found')
    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f'Job {job_id} is not completed (status: {job["status"]})')
    if not job.get('threshold_met'):
        raise HTTPException(
            status_code=400,
            detail=f'Job {job_id} did not meet the accuracy threshold — cannot deploy'
        )

    model      = job['model']
    final_acc  = job.get('final_accuracy') or float(job['accuracy'].rstrip('%'))

    dep = svc.deploy(model, job_id, final_acc, actor=body.actor)

    return {
        'message':    f'Successfully deployed {dep["version"]} for {model}',
        'deployment': _dep_out(dep),
    }


@router.post('/{dep_id}/rollback')
def rollback_deployment(dep_id: str, body: DeployRequest):
    """
    Rollback the model to its previous deployment version.
    """
    dep = ds.get_deployment(dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail='Deployment not found')
    if dep['status'] != 'active':
        raise HTTPException(status_code=400, detail='Only active deployments can be rolled back')
    if not dep.get('rollback_to'):
        raise HTTPException(status_code=400, detail='No previous version to roll back to')

    restored = svc.rollback(dep['model'], actor=body.actor)
    if not restored:
        raise HTTPException(status_code=400, detail='Rollback failed — no previous deployment found')

    return {
        'message':    f'Rolled back {dep["model"]} to {restored["version"]}',
        'deployment': _dep_out(restored),
    }


@router.post('/{dep_id}/stop')
def stop_deployment(dep_id: str, body: StopRequest):
    """
    Stop a deployment — takes the endpoint offline.
    Requires confirm=true in the request body.
    """
    if not body.confirm:
        raise HTTPException(
            status_code=400,
            detail='Send confirm=true to stop this deployment. This will take the endpoint offline.'
        )

    dep = ds.get_deployment(dep_id)
    if not dep:
        raise HTTPException(status_code=404, detail='Deployment not found')
    if dep['status'] != 'active':
        raise HTTPException(status_code=400, detail=f'Deployment is already {dep["status"]}')

    stopped = svc.stop_deployment(dep_id, actor=body.actor)
    return {
        'message':    f'{dep["version"]} for {dep["model"]} has been stopped',
        'deployment': _dep_out(stopped),
    }
