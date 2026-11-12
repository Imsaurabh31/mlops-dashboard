"""
Script runner — executes any training script as a subprocess and
streams its stdout into the job's metrics and logs.

Standard interface contract (all scripts must follow this):
  stdout line format:
    LOG    <message>              → appended to job['logs']
    METRIC <epoch> <train_acc> <val_acc> <train_loss> <val_loss>
                                  → appended to job['metrics'] + job['logs']
    DONE   <final_val_acc>        → training complete, sets final accuracy
    ERROR  <message>              → marks job as failed

To swap in a real training script:
  1. Write a script that follows the stdout interface above
  2. Update MODEL_SCRIPTS below to point to your script path
  3. No other changes needed — the pipeline is unaffected

"""
from __future__ import annotations
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services import store

# ── Script registry ──────────────────────────────────────────
# Change these paths to point to real training scripts when ready.
# The script must follow the stdout interface defined above.
_SCRIPTS_DIR = Path(__file__).parent.parent.parent / 'scripts'

MODEL_SCRIPTS: dict[str, Path] = {
    'gender': _SCRIPTS_DIR / 'dummy_training.py',
    'age':    _SCRIPTS_DIR / 'dummy_training.py',
    'staff':  _SCRIPTS_DIR / 'dummy_training.py',
}

# ── Model config (thresholds, task labels) ───────────────────
MODEL_CONFIG: dict[str, dict] = {
    'gender': {'task': 'Gender Classification', 'threshold': 90.0, 'architecture': 'ResNet-50'},
    'age':    {'task': 'Age Classification',     'threshold': 85.0, 'architecture': 'EfficientNet-B0'},
    'staff':  {'task': 'Staff Detection',        'threshold': 90.0, 'architecture': 'ResNet-34'},
}

TOTAL_EPOCHS = 20
DATA_DIR     = str(_SCRIPTS_DIR.parent / 'data')  # override with real path


def _ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


def _local_ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def _parse_metric_line(line: str) -> Optional[dict]:
    """
    Parse a METRIC stdout line from a training script.
    Format: METRIC <epoch> <train_acc> <val_acc> <train_loss> <val_loss>
    Returns a dict or None if the line is not a metric.
    """
    parts = line.strip().split()
    if len(parts) != 6 or parts[0] != 'METRIC':
        return None
    try:
        return {
            'epoch':      int(parts[1]),
            'train_acc':  float(parts[2]),
            'val_acc':    float(parts[3]),
            'train_loss': float(parts[4]),
            'val_loss':   float(parts[5]),
        }
    except ValueError:
        return None


def run_script(model_id: str, job_id: str, epochs: int = TOTAL_EPOCHS) -> None:
    """
    Run the training script for model_id as a subprocess.
    Streams stdout line by line into job['metrics'] and job['logs'].
    Always clears RUNNING_JOBS in a finally block.

    This is the ONLY function that needs to change when swapping scripts.
    Just update MODEL_SCRIPTS above — everything else stays the same.
    """
    cfg        = MODEL_CONFIG.get(model_id)
    script_path = MODEL_SCRIPTS.get(model_id)
    job        = store.get_job(job_id)

    if not cfg or not job:
        with store._running_jobs_lock:
            store.RUNNING_JOBS[model_id] = None
        return

    start_time = time.monotonic()

    try:
        job['logs'].append(f'[{_ts()}] Starting {cfg["task"]} training…')
        job['logs'].append(f'[{_ts()}] Script: {script_path.name}')
        job['logs'].append(f'[{_ts()}] Architecture: {cfg["architecture"]}')

        if not script_path.exists():
            raise FileNotFoundError(f'Training script not found: {script_path}')

        cmd = [
            sys.executable,       # use same Python interpreter
            str(script_path),
            '--model',     model_id,
            '--epochs',    str(epochs),
            '--data-dir',  DATA_DIR,
            '--threshold', str(cfg['threshold']),
        ]

        job['logs'].append(f'[{_ts()}] Command: {" ".join(cmd)}')

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,            # line-buffered
        )

        final_val_acc = None

        # Stream stdout line by line
        for raw_line in process.stdout:
            line = raw_line.strip()
            if not line:
                continue

            # Check cancellation
            if job.get('status') == 'cancelled':
                process.terminate()
                job['duration'] = f'{round(time.monotonic() - start_time)}s'
                return

            if line.startswith('METRIC '):
                m = _parse_metric_line(line)
                if m:
                    job['metrics'].append(m)
                    job['epoch'] = m['epoch']
                    job['logs'].append(
                        f'[{_ts()}] Epoch {m["epoch"]}/{epochs} — '
                        f'loss: {m["train_loss"]} — acc: {m["train_acc"]}% — '
                        f'val_loss: {m["val_loss"]} — val_acc: {m["val_acc"]}%'
                    )

            elif line.startswith('DONE '):
                try:
                    final_val_acc = float(line.split()[1])
                except (IndexError, ValueError):
                    pass
                job['logs'].append(f'[{_ts()}] Script reported: {line}')

            elif line.startswith('ERROR '):
                msg = line[6:]
                job['logs'].append(f'[{_ts()}] ❌ Script error: {msg}')
                process.wait()
                raise RuntimeError(f'Script error: {msg}')

            elif line.startswith('LOG '):
                job['logs'].append(f'[{_ts()}] {line[4:]}')

            else:
                # Pass through any other output
                job['logs'].append(f'[{_ts()}] {line}')

        # Capture stderr
        stderr_output = process.stderr.read().strip()
        if stderr_output:
            for err_line in stderr_output.splitlines():
                job['logs'].append(f'[{_ts()}] STDERR: {err_line}')

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f'Script exited with code {process.returncode}')

        # Use DONE value or fallback to last metric
        if final_val_acc is None and job['metrics']:
            final_val_acc = job['metrics'][-1]['val_acc']

        if final_val_acc is None:
            raise RuntimeError('Script completed but no metrics were produced')

        exceeded      = final_val_acc >= cfg['threshold']
        elapsed_s     = round(time.monotonic() - start_time)

        job['status']         = 'completed'
        job['accuracy']       = f'{final_val_acc}%'
        job['duration']       = f'{elapsed_s}s'
        job['threshold_met']  = exceeded
        job['final_accuracy'] = final_val_acc

        job['logs'].append(f'[{_ts()}] Training complete! Final val_acc: {final_val_acc}%')
        job['logs'].append(
            f'[{_ts()}] {"✅ Accuracy threshold met" if exceeded else "⚠️  Below threshold"} '
            f'({cfg["threshold"]}%). '
            f'{"Ready for deployment." if exceeded else "Review required."}'
        )

    except Exception as exc:
        elapsed_s = round(time.monotonic() - start_time)
        job['status']   = 'failed'
        job['duration'] = f'{elapsed_s}s'
        job['logs'].append(f'[{_ts()}] ❌ Training failed: {exc}')

    finally:
        with store._running_jobs_lock:
            store.RUNNING_JOBS[model_id] = None
