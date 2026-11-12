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

from app.routers import batches, training, images

app = FastAPI(
    title='OLY VISION MLOps API',
    description='Backend for the OLY VISION MLOps Dashboard. Handles image annotation, batch management and model auto-training.',
    version='0.1.0',
)

# ── CORS — allow the React dev server ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173',   # Vite dev server
        'http://localhost:4173',   # Vite preview
        'http://127.0.0.1:5173',
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ── Routers ────────────────────────────────────────────────
app.include_router(images.router,   prefix='/api')
app.include_router(batches.router,  prefix='/api')
app.include_router(training.router, prefix='/api')


@app.get('/')
def root():
    return {
        'service': 'OLY VISION MLOps API',
        'version': '0.1.0',
        'docs':    '/docs',
        'status':  'running',
    }


@app.get('/health')
def health():
    return {'status': 'ok'}
