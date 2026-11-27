"""
CRUD helpers — thin wrappers around SQLAlchemy queries.
Used by routers instead of direct store access.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.models import User, Batch, Image, TrainingJob, Deployment, DeployLog
from app.services.auth_store import hash_password, verify_password


# ── Users ─────────────────────────────────────────────────────
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session) -> List[User]:
    return db.query(User).all()


def create_user(db: Session, name: str, email: str, password: str, role: str) -> User:
    u = User(name=name, email=email.lower().strip(),
             password=hash_password(password), role=role)
    db.add(u); db.commit(); db.refresh(u)
    return u


def update_user(db: Session, user: User, **kwargs) -> User:
    if 'password' in kwargs:
        kwargs['password'] = hash_password(kwargs['password'])
    for k, v in kwargs.items():
        setattr(user, k, v)
    db.commit(); db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    u = get_user_by_email(db, email)
    if not u or not verify_password(password, u.password):
        return None
    u.last_login = datetime.now()
    db.commit()
    return u


# ── Batches ───────────────────────────────────────────────────
def list_batches(db: Session) -> List[Batch]:
    return db.query(Batch).order_by(Batch.id).all()


def get_batch(db: Session, batch_id: int) -> Optional[Batch]:
    return db.query(Batch).filter(Batch.id == batch_id).first()


def get_batch_by_name(db: Session, name: str) -> Optional[Batch]:
    return db.query(Batch).filter(Batch.name == name).first()


def create_batch(db: Session, name: str, client: str,
                 assignee: Optional[str], images: int) -> Batch:
    b = Batch(name=name, client=client, assigned=assignee,
              images=images, pct=0.0,
              status='in-progress' if assignee else 'unassigned')
    db.add(b); db.commit(); db.refresh(b)
    return b


def update_batch(db: Session, batch: Batch, **kwargs) -> Batch:
    for k, v in kwargs.items():
        setattr(batch, k, v)
    db.commit(); db.refresh(batch)
    return batch


def delete_batch(db: Session, batch: Batch) -> None:
    db.delete(batch); db.commit()


# ── Images ────────────────────────────────────────────────────
def list_images(db: Session, curated: Optional[bool] = None) -> List[Image]:
    q = db.query(Image)
    if curated is not None:
        q = q.filter(Image.curated == curated)
    return q.order_by(Image.id).all()


def get_image(db: Session, image_id: int) -> Optional[Image]:
    return db.query(Image).filter(Image.id == image_id).first()


def annotate_image(db: Session, image: Image, annotations: dict) -> Image:
    image.set_annotations(annotations)
    image.curated = True
    db.commit(); db.refresh(image)
    return image


def image_stats(db: Session) -> dict:
    total   = db.query(Image).count()
    curated = db.query(Image).filter(Image.curated == True).count()
    return {
        'total':   total,
        'curated': curated,
        'pending': total - curated,
        'pct':     round(curated / total * 100, 1) if total else 0,
    }


# ── Training Jobs ─────────────────────────────────────────────
def list_jobs(db: Session) -> List[TrainingJob]:
    return db.query(TrainingJob).order_by(TrainingJob.started.desc()).all()


def get_job(db: Session, job_id: str) -> Optional[TrainingJob]:
    return db.query(TrainingJob).filter(TrainingJob.id == job_id).first()


def upsert_job(db: Session, job_dict: dict) -> TrainingJob:
    """Insert or update a job from a dict (used by training service)."""
    import json as _json
    job = db.query(TrainingJob).filter(TrainingJob.id == job_dict['id']).first()
    if not job:
        job = TrainingJob(id=job_dict['id'])
        db.add(job)
    for k, v in job_dict.items():
        if k == 'metrics':
            job.metrics_json = _json.dumps(v)
        elif k == 'logs':
            job.logs_json = _json.dumps(v)
        elif hasattr(job, k):
            setattr(job, k, v)
    db.commit()
    return job


# ── Deployments ───────────────────────────────────────────────
def list_deployments(db: Session, status: Optional[str] = None) -> List[Deployment]:
    q = db.query(Deployment)
    if status:
        q = q.filter(Deployment.status == status)
    return q.order_by(Deployment.deployed_at.desc()).all()


def get_deployment(db: Session, dep_id: str) -> Optional[Deployment]:
    return db.query(Deployment).filter(Deployment.id == dep_id).first()


def get_active_deployment(db: Session, model: str) -> Optional[Deployment]:
    return db.query(Deployment).filter(
        Deployment.model == model,
        Deployment.status == 'active',
    ).first()


def save_deployment(db: Session, dep_dict: dict) -> Deployment:
    dep = get_deployment(db, dep_dict['id'])
    if not dep:
        dep = Deployment(id=dep_dict['id'])
        db.add(dep)
    for k, v in dep_dict.items():
        if hasattr(dep, k):
            setattr(dep, k, v)
    db.commit(); db.refresh(dep)
    return dep


def add_deploy_log(db: Session, action: str, model: str, detail: str, actor: str = 'system') -> None:
    from datetime import datetime as dt
    entry = DeployLog(
        timestamp=dt.now().strftime('%Y-%m-%d %H:%M'),
        action=action, model=model, detail=detail, actor=actor,
    )
    db.add(entry); db.commit()


def list_deploy_log(db: Session) -> List[DeployLog]:
    return db.query(DeployLog).order_by(DeployLog.id.desc()).all()
