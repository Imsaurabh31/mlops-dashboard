"""
Real inference endpoints using Thiyagu's ONNX models.

POST /api/infer/staff     — classify staff vs customer from image upload
POST /api/infer/id        — classify ID card visible vs not visible
GET  /api/infer/status    — model load status
POST /api/infer/batch     — run inference on a curation image by ID (uses placeholder pixel)
"""
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.inference_service import run_inference, model_status
from app.services.auth_service import get_current_user

router = APIRouter(prefix='/infer', tags=['Inference'])


@router.get('/status')
def inference_status():
    """Check which ONNX models are loaded and their file sizes."""
    return model_status()


@router.post('/staff')
async def infer_staff(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Classify an uploaded image as staff or customer.
    Uses lm_staff_convnext_atto (98.75% accuracy, 14MB).
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File must be an image')

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:   # 10 MB limit
        raise HTTPException(status_code=400, detail='Image too large (max 10 MB)')

    result = run_inference('staff', image_bytes)
    return {
        'filename':   file.filename,
        'prediction': result,
        'annotation': 'S' if result.get('is_staff') else 'N',
    }


@router.post('/id')
async def infer_id_card(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Classify whether an ID card is visible in an uploaded image.
    Uses lm_id_convnext_pico (98.25% accuracy, 34MB).
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File must be an image')

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail='Image too large (max 10 MB)')

    result = run_inference('id', image_bytes)
    return {
        'filename':   file.filename,
        'prediction': result,
        'annotation': 'Y' if result.get('is_visible') else 'N',
    }


@router.post('/suggest/{image_id}')
async def suggest_annotations(
    image_id: int,
    current_user: dict = Depends(get_current_user),
):
    """
    Return VLM-style annotation suggestions for a curation image.
    Currently uses model status to decide what to suggest.
    When real CCTV images are stored, this will run full inference.
    """
    status = model_status()
    staff_ready = status.get('staff', {}).get('exists', False)
    id_ready    = status.get('id',    {}).get('exists', False)

    return {
        'image_id':     image_id,
        'suggestions': {
            'staff': {
                'available':  staff_ready,
                'model':      'lm_staff_convnext_atto',
                'note':       'Ready — upload real image to /api/infer/staff for prediction' if staff_ready else 'Model not loaded',
            },
            'id': {
                'available':  id_ready,
                'model':      'lm_id_convnext_pico',
                'note':       'Ready — upload real image to /api/infer/id for prediction' if id_ready else 'Model not loaded',
            },
        },
        'note': 'Full auto-suggestion available once real CCTV images are stored in the backend',
    }
