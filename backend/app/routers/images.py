"""Image / annotation endpoints."""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import ImageOut, ImageAnnotateRequest
from app.services import store

router = APIRouter(prefix='/images', tags=['Images'])


def _img_to_out(img: dict) -> ImageOut:
    return ImageOut(
        id=img['id'], label=img['label'], location=img['location'],
        curated=img['curated'], annotations=img.get('annotations'),
        timestamp=img['timestamp'],
    )


# IMPORTANT: /stats/summary MUST be declared before /{image_id}
# otherwise FastAPI matches 'stats' as an integer image_id and returns 422
@router.get('/stats/summary')
def image_stats():
    """Return curated/pending counts for the dashboard."""
    total   = len(store.IMAGES)
    curated = sum(1 for i in store.IMAGES if i['curated'])
    return {
        'total':   total,
        'curated': curated,
        'pending': total - curated,
        'pct':     round(curated / total * 100, 1) if total else 0,
    }


@router.get('/', response_model=List[ImageOut])
def list_images(
    curated: Optional[bool] = Query(None, description='Filter by curated status'),
    batch_id: Optional[int] = Query(None, description='Filter by batch (not yet implemented — ignored)'),
):
    imgs = store.IMAGES
    if curated is not None:
        imgs = [i for i in imgs if i['curated'] == curated]
    # batch_id filter: placeholder for when images are linked to batches in DB
    return [_img_to_out(i) for i in imgs]


@router.get('/{image_id}', response_model=ImageOut)
def get_image(image_id: int):
    img = next((i for i in store.IMAGES if i['id'] == image_id), None)
    if not img:
        raise HTTPException(status_code=404, detail='Image not found')
    return _img_to_out(img)


@router.post('/{image_id}/annotate', response_model=ImageOut)
def annotate_image(image_id: int, body: ImageAnnotateRequest):
    """Save annotations for an image and mark it as curated."""
    img = next((i for i in store.IMAGES if i['id'] == image_id), None)
    if not img:
        raise HTTPException(status_code=404, detail='Image not found')
    if body.image_id != image_id:
        raise HTTPException(status_code=400, detail='image_id in body does not match URL')

    img['annotations'] = body.annotations.model_dump()
    img['curated']     = True
    return _img_to_out(img)
