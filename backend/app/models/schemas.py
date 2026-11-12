"""
Pydantic schemas for request/response validation.
Replace with real DB models once a database is attached.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ── Annotation ──────────────────────────────────────────────
class Annotation(BaseModel):
    gender: Optional[Literal['M', 'F', 'R']] = None
    age:    Optional[Literal['1', '2', '3', '4', '5', '6', 'R']] = None
    staff:  Optional[Literal['S', 'N', 'R']] = None
    id:     Optional[Literal['Y', 'N', 'R']] = None


class ImageAnnotateRequest(BaseModel):
    image_id:    int
    annotations: Annotation


class ImageOut(BaseModel):
    id:          int
    label:       str
    location:    str
    curated:     bool
    annotations: Optional[Annotation] = None
    timestamp:   str


# ── Batch ────────────────────────────────────────────────────
class BatchStatus(str, Enum):
    """Real enum — use BatchStatus.COMPLETED etc. for comparisons."""
    UNASSIGNED  = 'unassigned'
    IN_PROGRESS = 'in-progress'
    COMPLETED   = 'completed'


class BatchCreate(BaseModel):
    name:     str = Field(..., min_length=1)
    client:   str = Field(..., min_length=1)
    assignee: Optional[str] = None   # maps to 'assigned' in store
    images:   int = Field(..., gt=0)


class BatchUpdate(BaseModel):
    name:     Optional[str] = None
    client:   Optional[str] = None
    assignee: Optional[str] = None   # None = don't change; empty string = unassign
    images:   Optional[int] = Field(None, gt=0)


class BatchOut(BaseModel):
    id:       int
    name:     str
    client:   str
    assigned: Optional[str] = None
    images:   int
    pct:      float
    status:   str


# ── Training Job ─────────────────────────────────────────────
class JobStatus(str, Enum):
    """Real enum for training job status."""
    QUEUED    = 'queued'
    RUNNING   = 'running'
    COMPLETED = 'completed'
    FAILED    = 'failed'
    CANCELLED = 'cancelled'


class TrainingMetric(BaseModel):
    """snake_case to match backend dict keys — frontend must use val_acc not valAcc."""
    epoch:      int
    train_acc:  float
    val_acc:    float
    train_loss: float
    val_loss:   float


class TrainingJobOut(BaseModel):
    id:              str
    model:           str
    task:            str
    status:          str
    started:         str
    duration:        str
    accuracy:        str
    epoch:           int = 0
    threshold_met:   bool = False
    final_accuracy:  Optional[float] = None
    triggered_by:    Optional[str] = None


class TrainingJobDetail(TrainingJobOut):
    metrics: List[TrainingMetric] = []
    logs:    List[str] = []


# ── Trigger ──────────────────────────────────────────────────
class TriggerTrainingRequest(BaseModel):
    model_config = {'protected_namespaces': ()}
    batch_id:  int
    model_ids: List[Literal['gender', 'age', 'staff']] = ['gender', 'age', 'staff']
