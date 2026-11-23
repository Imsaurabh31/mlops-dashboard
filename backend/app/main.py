"""
OLY VISION — MLOps Backend
FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000

API docs:
    http://localhost:8000/docs
    http://localhost:8000/redoc
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import batches, training, images, quality

app = FastAPI(
    title='OLY VISION MLOps API',
    description='Backend for the OLY VISION MLOps Dashboard.',
    version='0.2.0',
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',
        'http://localhost:4173',
        'http://127.0.0.1:5173',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(images.router,   prefix='/api')
app.include_router(batches.router,  prefix='/api')
app.include_router(training.router, prefix='/api')
app.include_router(quality.router,  prefix='/api')


@app.get('/')
def root():
    return {
        'service': 'OLY VISION MLOps API',
        'version': '0.2.0',
        'docs':    '/docs',
        'status':  'running',
    }


@app.get('/health')
def health():
    return {'status': 'ok'}
