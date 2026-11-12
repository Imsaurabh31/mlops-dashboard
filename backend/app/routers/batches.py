"""Batch management endpoints."""
from __future__ import annotations
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import BatchCreate, BatchUpdate, BatchOut
from app.services import store
from app.services.training_service import trigger_on_batch_completion

router = APIRouter(prefix='/batches', tags=['Batches'])


def _batch_to_out(b: dict) -> BatchOut:
    return BatchOut(
        id=b['id'], name=b['name'], client=b['client'],
        assigned=b.get('assigned'), images=b['images'],
        pct=b['pct'], status=b['status'],
    )


@router.get('/', response_model=List[BatchOut])
def list_batches():
    return [_batch_to_out(b) for b in store.BATCHES]


@router.post('/', response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(body: BatchCreate):
    if any(b['name'].lower() == body.name.strip().lower() for b in store.BATCHES):
        raise HTTPException(status_code=409, detail=f'Batch name "{body.name}" already exists')

    new_batch = {
        'id':       store.next_batch_id(),
        'name':     body.name.strip(),
        'client':   body.client.strip(),
        'assigned': body.assignee or None,
        'images':   body.images,
        'pct':      0.0,
        'status':   'in-progress' if body.assignee else 'unassigned',
    }
    store.BATCHES.insert(0, new_batch)
    return _batch_to_out(new_batch)


@router.get('/{batch_id}', response_model=BatchOut)
def get_batch(batch_id: int):
    batch = next((b for b in store.BATCHES if b['id'] == batch_id), None)
    if not batch:
        raise HTTPException(status_code=404, detail='Batch not found')
    return _batch_to_out(batch)


@router.patch('/{batch_id}', response_model=BatchOut)
def update_batch(batch_id: int, body: BatchUpdate):
    batch = next((b for b in store.BATCHES if b['id'] == batch_id), None)
    if not batch:
        raise HTTPException(status_code=404, detail='Batch not found')

    if body.name is not None:
        if any(b['name'].lower() == body.name.strip().lower() and b['id'] != batch_id
               for b in store.BATCHES):
            raise HTTPException(status_code=409, detail=f'Batch name "{body.name}" already exists')
        batch['name'] = body.name.strip()

    if body.client is not None:
        batch['client'] = body.client.strip()

    # assignee: None = don't change; empty string '' = unassign
    if body.assignee is not None:
        batch['assigned'] = body.assignee.strip() or None

    if body.images is not None:
        batch['images'] = body.images
        # Recompute pct when image count changes (Issue 16 fix)
        # pct stays the same ratio, just capped at 100
        batch['pct'] = min(100.0, batch['pct'])

    # Recompute status
    if not batch['assigned']:
        batch['status'] = 'unassigned'
    elif batch['pct'] >= 100:
        batch['status'] = 'completed'
    else:
        batch['status'] = 'in-progress'

    return _batch_to_out(batch)


@router.delete('/{batch_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_batch(batch_id: int):
    idx = next((i for i, b in enumerate(store.BATCHES) if b['id'] == batch_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail='Batch not found')
    store.BATCHES.pop(idx)


@router.post('/{batch_id}/complete')
def complete_batch(batch_id: int):
    """
    Mark a batch as 100% curated → auto-triggers training for all 3 models.
    This is the key endpoint for the batch-completion → auto-training pipeline.
    """
    batch = next((b for b in store.BATCHES if b['id'] == batch_id), None)
    if not batch:
        raise HTTPException(status_code=404, detail='Batch not found')

    batch['pct']    = 100.0
    batch['status'] = 'completed'

    jobs = trigger_on_batch_completion(batch_id)

    return {
        'message':      f'Batch "{batch["name"]}" marked complete. Training triggered.',
        'batch_id':     batch_id,
        'jobs_started': [
            {'id': j['id'], 'model': j['model'], 'status': j['status'], 'triggered_by': j.get('triggered_by')}
            for j in jobs
        ],
    }
