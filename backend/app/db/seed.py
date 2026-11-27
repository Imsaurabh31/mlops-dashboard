"""
Database seeder — creates tables and populates initial data.
Runs automatically on app startup if the database is empty.
Safe to run multiple times (idempotent).
"""
from __future__ import annotations
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import engine, Base
from app.db.models import User, Batch, Image, TrainingJob, Deployment, DeployLog
from app.services.auth_store import hash_password


def _ts():
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def init_db():
    """Create all tables. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)


def seed_db(db: Session) -> None:
    """Seed initial data if tables are empty."""

    # ── Users ────────────────────────────────────────────────
    if db.query(User).count() == 0:
        users = [
            User(id=1, name='Admin User',  email='admin@oly.com',  password=hash_password('admin123'),   role='admin',   active=True, created_at=datetime(2026,10,1,9,0)),
            User(id=2, name='Alice Chen',  email='alice@oly.com',  password=hash_password('curator123'), role='curator', active=True, created_at=datetime(2026,10,5,10,0)),
            User(id=3, name='Bob Smith',   email='bob@oly.com',    password=hash_password('curator123'), role='curator', active=True, created_at=datetime(2026,10,5,10,0)),
            User(id=4, name='Carol Davis', email='carol@oly.com',  password=hash_password('curator123'), role='curator', active=True, created_at=datetime(2026,10,5,10,0)),
            User(id=5, name='View User',   email='viewer@oly.com', password=hash_password('viewer123'),  role='viewer',  active=True, created_at=datetime(2026,10,10,11,0)),
        ]
        db.bulk_save_objects(users)
        db.commit()
        print('  Seeded users')

    # ── Batches ──────────────────────────────────────────────
    if db.query(Batch).count() == 0:
        batches = [
            Batch(id=1, name='Batch-001', client='RetailCo',  assigned='alice@oly.com', images=500, pct=100.0, status='completed'),
            Batch(id=2, name='Batch-002', client='ShopMart',  assigned='bob@oly.com',   images=480, pct=72.0,  status='in-progress'),
            Batch(id=3, name='Batch-003', client='FreshMart', assigned='carol@oly.com', images=320, pct=45.0,  status='in-progress'),
            Batch(id=4, name='Batch-004', client='RetailCo',  assigned='bob@oly.com',   images=600, pct=10.0,  status='in-progress'),
            Batch(id=5, name='Batch-005', client='MegaStore', assigned=None,            images=400, pct=0.0,   status='unassigned'),
            Batch(id=6, name='Batch-006', client='FreshMart', assigned='alice@oly.com', images=550, pct=88.0,  status='in-progress'),
        ]
        db.bulk_save_objects(batches)
        db.commit()
        print('  Seeded batches')

    # ── Images ───────────────────────────────────────────────
    if db.query(Image).count() == 0:
        LOCATIONS = ['Store Entrance', 'Aisle 3', 'Checkout', 'Parking Lot', 'Lobby']
        PRESET = [
            {'gender': 'M', 'age': '4', 'staff': 'S', 'id': 'Y'},
            {'gender': 'F', 'age': '5', 'staff': 'N', 'id': 'N'},
            {'gender': 'M', 'age': '3', 'staff': 'N', 'id': 'N'},
            {'gender': 'F', 'age': '4', 'staff': 'S', 'id': 'Y'},
            {'gender': 'M', 'age': '5', 'staff': 'N', 'id': 'N'},
        ]
        images = []
        for i in range(24):
            img = Image(
                id        = i + 1,
                label     = f'IMG_{str(i+1).zfill(4)}',
                location  = LOCATIONS[i % 5],
                curated   = i < 5,
                timestamp = f'2026-10-{str(28-(i%3)).zfill(2)} {str(10+(i%12)).zfill(2)}:{str(i*3%60).zfill(2)}',
                batch_id  = (i % 6) + 1,
            )
            if i < 5:
                img.annotations_json = json.dumps(PRESET[i])
            images.append(img)
        db.bulk_save_objects(images)
        db.commit()
        print('  Seeded images')

    # ── Training Jobs ────────────────────────────────────────
    if db.query(TrainingJob).count() == 0:
        jobs = [
            TrainingJob(id='JOB-1024', model='gender', task='Gender Classification', status='completed', started='2026-10-28 09:14', duration='4m 32s', accuracy='92.4%', epoch=20, threshold_met=True,  final_accuracy=92.4),
            TrainingJob(id='JOB-1022', model='staff',  task='Staff Detection',       status='completed', started='2026-10-27 18:02', duration='6m 11s', accuracy='95.1%', epoch=20, threshold_met=True,  final_accuracy=95.1),
            TrainingJob(id='JOB-1021', model='gender', task='Gender Classification', status='failed',    started='2026-10-27 14:30', duration='1m 03s', accuracy='—',     epoch=3,  threshold_met=False, final_accuracy=None),
            TrainingJob(id='JOB-1020', model='age',    task='Age Classification',    status='completed', started='2026-10-26 11:00', duration='5m 48s', accuracy='86.9%', epoch=20, threshold_met=True,  final_accuracy=86.9),
        ]
        db.bulk_save_objects(jobs)
        db.commit()
        print('  Seeded training jobs')

    # ── Deployments ──────────────────────────────────────────
    if db.query(Deployment).count() == 0:
        deps = [
            Deployment(id='DEP-001', model='gender', task='Gender Classification', version='v1', job_id='JOB-1024', accuracy=92.4, status='active', endpoint='/api/infer/gender', deployed_at='2026-10-28 10:00', deployed_by='admin', latency_ms=18, requests_hr=1200, uptime_pct=99.8, health='healthy'),
            Deployment(id='DEP-002', model='staff',  task='Staff Detection',       version='v1', job_id='JOB-1022', accuracy=95.1, status='active', endpoint='/api/infer/staff',  deployed_at='2026-10-27 19:00', deployed_by='admin', latency_ms=22, requests_hr=1200, uptime_pct=99.9, health='healthy'),
            Deployment(id='DEP-003', model='age',    task='Age Classification',    version='v1', job_id='JOB-1020', accuracy=86.9, status='active', endpoint='/api/infer/age',    deployed_at='2026-10-26 12:00', deployed_by='admin', latency_ms=25, requests_hr=1200, uptime_pct=99.5, health='healthy'),
        ]
        db.bulk_save_objects(deps)
        db.commit()
        print('  Seeded deployments')

    print('  Database ready')
