"""
OLY VISION — MLOps Backend  v0.3.0
FastAPI application entry point.

Run:
    uvicorn app.main:app --reload --port 8000

Docs:
    http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import images, batches, training, quality, deployment
from app.routers import auth

app = FastAPI(
    title='OLY VISION MLOps API',
    description='Backend for the OLY VISION MLOps Dashboard — Stage 1, 2, 3 & 4.',
    version='0.4.0',
)

# ── CORS ─────────────────────────────────────────────────────
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

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router,       prefix='/api')
app.include_router(images.router,     prefix='/api')
app.include_router(batches.router,    prefix='/api')
app.include_router(training.router,   prefix='/api')
app.include_router(quality.router,    prefix='/api')
app.include_router(deployment.router, prefix='/api')


@app.get('/')
def root():
    return {
        'service': 'OLY VISION MLOps API',
        'version': '0.4.0',
        'docs':    '/docs',
        'status':  'running',
    }


@app.get('/health')
def health():
    return {'status': 'ok'}
