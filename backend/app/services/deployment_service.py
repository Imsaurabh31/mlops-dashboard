"""
Deployment service — handles auto-deployment, rollback and health checks.

Auto-deploy flow:
  1. Training completes with accuracy >= threshold
  2. training_service calls auto_deploy_if_eligible()
  3. Previous active deployment is archived
  4. New deployment is created and set as active
  5. Deployment log entry added

Rollback flow:
  1. rollback(model) finds previous deployment
  2. Current active is archived
  3. Previous deployment is restored as active
"""
from __future__ import annotations
import time
from datetime import datetime
from typing import Optional

from app.services import deployment_store as ds

ENDPOINTS = {
    'gender': '/api/infer/gender',
    'age':    '/api/infer/age',
    'staff':  '/api/infer/staff',
}

TASK_NAMES = {
    'gender': 'Gender Classification',
    'age':    'Age Classification',
    'staff':  'Staff Detection',
}


def _ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def _next_version(model: str) -> str:
    """Generate next version string for a model e.g. v1 → v2 → v3."""
    model_deps = [d for d in ds.DEPLOYMENTS if d['model'] == model]
    if not model_deps:
        return 'v1'
    # Parse highest version number
    versions = []
    for d in model_deps:
        try:
            versions.append(int(d['version'].lstrip('v')))
        except ValueError:
            pass
    return f'v{max(versions) + 1}' if versions else 'v1'


def deploy(
    model: str,
    job_id: str,
    accuracy: float,
    actor: str = 'auto',
) -> dict:
    """
    Deploy a trained model.
    Archives the current active deployment and creates a new one.
    Returns the new deployment dict.
    """
    # Archive current active
    current = ds.get_active(model)
    if current:
        current['status']    = 'archived'
        current['health']    = 'archived'

    version  = _next_version(model)
    dep_id   = ds.next_deploy_id()
    prev_id  = current['id'] if current else None

    new_dep = {
        'id':            dep_id,
        'model':         model,
        'task':          TASK_NAMES.get(model, model),
        'version':       version,
        'job_id':        job_id,
        'accuracy':      accuracy,
        'status':        'active',
        'endpoint':      ENDPOINTS.get(model, f'/api/infer/{model}'),
        'deployed_at':   _ts(),
        'deployed_by':   actor,
        'latency_ms':    _simulate_latency(model),
        'requests_hr':   0,
        'uptime_pct':    100.0,
        'health':        'healthy',
        'last_checked':  _ts(),
        'rollback_to':   prev_id,
    }

    ds.DEPLOYMENTS.insert(0, new_dep)
    ds.ACTIVE[model] = dep_id

    ds.add_log(
        action='deploy',
        model=model,
        detail=f'{version} deployed (accuracy {accuracy}%, job {job_id})',
        actor=actor,
    )

    return new_dep


def auto_deploy_if_eligible(model: str, job_id: str, final_accuracy: float, threshold: float) -> Optional[dict]:
    """
    Called by training_service after training completes.
    Deploys automatically if accuracy >= threshold.
    Returns the new deployment or None if below threshold.
    """
    if final_accuracy < threshold:
        ds.add_log(
            action='auto_deploy_skipped',
            model=model,
            detail=f'Accuracy {final_accuracy}% below threshold {threshold}% — not deployed',
        )
        return None

    return deploy(model, job_id, final_accuracy, actor='auto')


def rollback(model: str, actor: str = 'admin') -> Optional[dict]:
    """
    Rollback to the previous deployment for a model.
    Returns the restored deployment or None if no previous exists.
    """
    current = ds.get_active(model)
    if not current:
        return None

    prev_id = current.get('rollback_to')
    if not prev_id:
        return None

    prev = ds.get_deployment(prev_id)
    if not prev:
        return None

    # Archive current
    current['status'] = 'archived'
    current['health'] = 'archived'

    # Restore previous
    prev['status']       = 'active'
    prev['health']       = 'healthy'
    prev['last_checked'] = _ts()
    ds.ACTIVE[model]     = prev_id

    ds.add_log(
        action='rollback',
        model=model,
        detail=f'Rolled back from {current["version"]} to {prev["version"]}',
        actor=actor,
    )

    return prev


def stop_deployment(dep_id: str, actor: str = 'admin') -> Optional[dict]:
    """
    Stop a deployment — takes the endpoint offline.
    Requires confirmation (handled at the API layer).
    """
    dep = ds.get_deployment(dep_id)
    if not dep:
        return None

    dep['status'] = 'stopped'
    dep['health'] = 'offline'

    if ds.ACTIVE.get(dep['model']) == dep_id:
        ds.ACTIVE[dep['model']] = None

    ds.add_log(
        action='stop',
        model=dep['model'],
        detail=f'{dep["version"]} stopped',
        actor=actor,
    )

    return dep


def refresh_health() -> None:
    """
    Simulate health check for all active deployments.
    Replace with real endpoint ping when available.
    """
    import random
    for dep in ds.DEPLOYMENTS:
        if dep['status'] != 'active':
            continue
        # Simulate slight latency variance
        dep['latency_ms']   = max(10, dep['latency_ms'] + random.randint(-3, 3))
        dep['requests_hr']  = max(0, dep['requests_hr'] + random.randint(-50, 100))
        dep['uptime_pct']   = round(min(100, dep['uptime_pct'] + random.uniform(-0.1, 0.05)), 2)
        dep['health']       = 'healthy' if dep['uptime_pct'] > 95 else 'degraded'
        dep['last_checked'] = _ts()


def _simulate_latency(model: str) -> int:
    """Placeholder — replace with real endpoint latency measurement."""
    return {'gender': 18, 'age': 25, 'staff': 22}.get(model, 20)
