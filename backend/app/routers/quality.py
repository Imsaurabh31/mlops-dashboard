"""
Annotation Quality Score — Idea 2.

Calculates a confidence / agreement score for each annotated image.
Images where annotations look inconsistent with the batch majority
are flagged for re-review.

Endpoints:
  GET /api/quality/scores       — quality score for every curated image
  GET /api/quality/flagged      — images that need re-review
  GET /api/quality/summary      — overall quality stats
  POST /api/quality/{image_id}/approve   — approve a flagged image
  POST /api/quality/{image_id}/flag      — manually flag an image
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from app.services import store

router = APIRouter(prefix='/quality', tags=['Quality'])

# Fields used for agreement calculation
ANN_FIELDS = ['gender', 'age', 'staff', 'id']

# Threshold below which an image is auto-flagged (0–100)
FLAG_THRESHOLD = 60.0

# In-memory review status store {image_id: 'approved' | 'flagged' | None}
REVIEW_STATUS: dict[int, Optional[str]] = {}


def _majority_vote(images: list[dict], field: str) -> Optional[str]:
    """Return the majority annotation value for a field across all curated images."""
    counts: dict[str, int] = {}
    for img in images:
        ann = img.get('annotations') or {}
        val = ann.get(field)
        if val and val != 'R':   # ignore rejected
            counts[val] = counts.get(val, 0) + 1
    if not counts:
        return None
    return max(counts, key=lambda k: counts[k])


def _compute_score(img: dict, majority: dict[str, Optional[str]]) -> float:
    """
    Score 0–100 based on how many of the image's annotations
    agree with the batch majority.
    Rejected ('R') annotations reduce the score.
    """
    ann = img.get('annotations') or {}
    if not any(ann.values()):
        return 0.0

    scored_fields = 0
    agreement     = 0

    for field in ANN_FIELDS:
        val = ann.get(field)
        maj = majority.get(field)
        if val is None:
            continue
        scored_fields += 1
        if val == 'R':
            agreement += 0.3   # partial credit — deliberate rejection
        elif val == maj:
            agreement += 1.0   # full agreement
        else:
            agreement += 0.0   # disagreement

    if scored_fields == 0:
        return 0.0
    return round((agreement / scored_fields) * 100, 1)


def _build_scores(images: list[dict]) -> list[dict]:
    curated = [i for i in images if i['curated'] and i.get('annotations')]
    if not curated:
        return []

    majority = {f: _majority_vote(curated, f) for f in ANN_FIELDS}

    result = []
    for img in curated:
        score  = _compute_score(img, majority)
        status = REVIEW_STATUS.get(img['id'])
        flagged = (score < FLAG_THRESHOLD or status == 'flagged') and status != 'approved'

        ann = img.get('annotations') or {}
        result.append({
            'image_id':   img['id'],
            'label':      img['label'],
            'location':   img['location'],
            'score':      score,
            'flagged':    flagged,
            'status':     status or ('flagged' if flagged else 'ok'),
            'annotations': ann,
            'majority':   majority,
            'disagreements': [
                f for f in ANN_FIELDS
                if ann.get(f) and ann.get(f) != 'R' and majority.get(f) and ann.get(f) != majority.get(f)
            ],
        })

    return sorted(result, key=lambda x: x['score'])   # lowest scores first


@router.get('/scores')
def quality_scores():
    """Quality score for every curated image. Sorted lowest (worst) first."""
    return _build_scores(store.IMAGES)


@router.get('/flagged')
def flagged_images():
    """Images flagged for re-review — either low score or manually flagged."""
    all_scores = _build_scores(store.IMAGES)
    return [s for s in all_scores if s['flagged']]


@router.get('/summary')
def quality_summary():
    """Overall annotation quality stats."""
    scores = _build_scores(store.IMAGES)
    if not scores:
        return {'total': 0, 'flagged': 0, 'approved': 0, 'avg_score': 0, 'quality_pct': 0}

    total    = len(scores)
    flagged  = sum(1 for s in scores if s['flagged'])
    approved = sum(1 for s in scores if s['status'] == 'approved')
    avg      = round(sum(s['score'] for s in scores) / total, 1)

    return {
        'total':       total,
        'flagged':     flagged,
        'approved':    approved,
        'ok':          total - flagged,
        'avg_score':   avg,
        'quality_pct': round(((total - flagged) / total) * 100, 1),
    }


@router.post('/{image_id}/approve')
def approve_image(image_id: int):
    """Approve a flagged image — removes it from the re-review queue."""
    img = next((i for i in store.IMAGES if i['id'] == image_id), None)
    if not img:
        raise HTTPException(status_code=404, detail='Image not found')
    if not img['curated']:
        raise HTTPException(status_code=400, detail='Image has not been annotated yet')
    REVIEW_STATUS[image_id] = 'approved'
    return {'image_id': image_id, 'status': 'approved'}


@router.post('/{image_id}/flag')
def flag_image(image_id: int):
    """Manually flag an image for re-review."""
    img = next((i for i in store.IMAGES if i['id'] == image_id), None)
    if not img:
        raise HTTPException(status_code=404, detail='Image not found')
    REVIEW_STATUS[image_id] = 'flagged'
    return {'image_id': image_id, 'status': 'flagged'}
