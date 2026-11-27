"""
SQLAlchemy ORM models — maps Python classes to SQLite tables.

Tables:
  users       — user accounts with roles
  batches     — annotation batches
  images      — images and their annotations
  training_jobs — training job history
  deployments — model deployment registry
  deploy_log  — deployment audit log
"""
from __future__ import annotations
import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def _now() -> datetime:
    return datetime.now()


# ── Users ─────────────────────────────────────────────────────
class User(Base):
    __tablename__ = 'users'

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(200), unique=True, nullable=False, index=True)
    password   = Column(String(200), nullable=False)   # bcrypt hash
    role       = Column(String(20),  nullable=False, default='curator')
    active     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'email':      self.email,
            'role':       self.role,
            'active':     self.active,
            'created_at': str(self.created_at),
            'last_login': str(self.last_login) if self.last_login else None,
        }


# ── Batches ───────────────────────────────────────────────────
class Batch(Base):
    __tablename__ = 'batches'

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), unique=True, nullable=False)
    client     = Column(String(100), nullable=False)
    assigned   = Column(String(200), nullable=True)   # curator email
    images     = Column(Integer, nullable=False)
    pct        = Column(Float, default=0.0)
    status     = Column(String(30), default='unassigned')
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        return {
            'id':       self.id,
            'name':     self.name,
            'client':   self.client,
            'assigned': self.assigned,
            'images':   self.images,
            'pct':      self.pct,
            'status':   self.status,
        }


# ── Images ────────────────────────────────────────────────────
class Image(Base):
    __tablename__ = 'images'

    id               = Column(Integer, primary_key=True, index=True)
    label            = Column(String(50), unique=True, nullable=False)
    location         = Column(String(100), nullable=False)
    curated          = Column(Boolean, default=False)
    annotations_json = Column(Text, nullable=True)   # JSON string
    timestamp        = Column(String(20), nullable=False)
    batch_id         = Column(Integer, ForeignKey('batches.id'), nullable=True)

    def get_annotations(self):
        if not self.annotations_json:
            return None
        try:
            return json.loads(self.annotations_json)
        except Exception:
            return None

    def set_annotations(self, ann: dict | None):
        self.annotations_json = json.dumps(ann) if ann else None

    def to_dict(self):
        return {
            'id':          self.id,
            'label':       self.label,
            'location':    self.location,
            'curated':     self.curated,
            'annotations': self.get_annotations(),
            'timestamp':   self.timestamp,
        }


# ── Training Jobs ─────────────────────────────────────────────
class TrainingJob(Base):
    __tablename__ = 'training_jobs'

    id              = Column(String(20),  primary_key=True)
    model           = Column(String(30),  nullable=False)
    task            = Column(String(100), nullable=False)
    status          = Column(String(20),  default='running')
    started         = Column(String(20),  nullable=False)
    duration        = Column(String(20),  default='—')
    accuracy        = Column(String(20),  default='—')
    epoch           = Column(Integer,     default=0)
    threshold_met   = Column(Boolean,     default=False)
    final_accuracy  = Column(Float,       nullable=True)
    triggered_by    = Column(String(50),  nullable=True)
    metrics_json    = Column(Text,        default='[]')
    logs_json       = Column(Text,        default='[]')
    deployment_id   = Column(String(20),  nullable=True)

    def get_metrics(self):
        try: return json.loads(self.metrics_json or '[]')
        except: return []

    def get_logs(self):
        try: return json.loads(self.logs_json or '[]')
        except: return []

    def to_dict(self):
        return {
            'id':             self.id,
            'model':          self.model,
            'task':           self.task,
            'status':         self.status,
            'started':        self.started,
            'duration':       self.duration,
            'accuracy':       self.accuracy,
            'epoch':          self.epoch,
            'threshold_met':  self.threshold_met,
            'final_accuracy': self.final_accuracy,
            'triggered_by':   self.triggered_by,
            'metrics':        self.get_metrics(),
            'logs':           self.get_logs(),
        }


# ── Deployments ───────────────────────────────────────────────
class Deployment(Base):
    __tablename__ = 'deployments'

    id           = Column(String(20),  primary_key=True)
    model        = Column(String(30),  nullable=False)
    task         = Column(String(100), nullable=False)
    version      = Column(String(10),  nullable=False)
    job_id       = Column(String(20),  nullable=False)
    accuracy     = Column(Float,       nullable=False)
    status       = Column(String(20),  default='active')
    endpoint     = Column(String(100), nullable=False)
    deployed_at  = Column(String(20),  nullable=False)
    deployed_by  = Column(String(50),  default='system')
    latency_ms   = Column(Integer,     default=20)
    requests_hr  = Column(Integer,     default=0)
    uptime_pct   = Column(Float,       default=100.0)
    health       = Column(String(20),  default='healthy')
    last_checked = Column(String(20),  nullable=True)
    rollback_to  = Column(String(20),  nullable=True)

    def to_dict(self):
        return {
            'id':           self.id,
            'model':        self.model,
            'task':         self.task,
            'version':      self.version,
            'job_id':       self.job_id,
            'accuracy':     self.accuracy,
            'status':       self.status,
            'endpoint':     self.endpoint,
            'deployed_at':  self.deployed_at,
            'deployed_by':  self.deployed_by,
            'latency_ms':   self.latency_ms,
            'requests_hr':  self.requests_hr,
            'uptime_pct':   self.uptime_pct,
            'health':       self.health,
            'last_checked': self.last_checked,
            'rollback_to':  self.rollback_to,
        }


# ── Deployment Log ────────────────────────────────────────────
class DeployLog(Base):
    __tablename__ = 'deploy_log'

    id        = Column(Integer,     primary_key=True, autoincrement=True)
    timestamp = Column(String(20),  nullable=False)
    action    = Column(String(30),  nullable=False)
    model     = Column(String(30),  nullable=False)
    detail    = Column(Text,        nullable=False)
    actor     = Column(String(50),  default='system')

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'action':    self.action,
            'model':     self.model,
            'detail':    self.detail,
            'actor':     self.actor,
        }
