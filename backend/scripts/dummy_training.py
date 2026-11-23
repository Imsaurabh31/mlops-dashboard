#!/usr/bin/env python3
"""
Dummy training script — follows the standard OLY VISION training interface.

Standard interface (must be followed by ALL training scripts):
  Input  : command-line arguments  --model  --epochs  --data-dir  --threshold
  Output : stdout lines in one of these formats:
             LOG   <message>
             METRIC <epoch> <train_acc> <val_acc> <train_loss> <val_loss>
             DONE  <final_val_acc>
             ERROR <message>

To swap in a real script:
  1. Copy this file and rename it (e.g. resnet_gender.py)
  2. Replace the simulate_epoch() function with real training code
  3. Keep the same stdout format — the pipeline reads it unchanged
  4. Register the script path in MODEL_CONFIG inside script_runner.py

Usage:
  python scripts/dummy_training.py --model gender --epochs 20 --data-dir ./data
"""
import argparse
import random
import sys
import time

DUMMY_CONFIG = {
    'gender': {'target_acc': 92.4, 'architecture': 'ResNet-50'},
    'age':    {'target_acc': 87.3, 'architecture': 'EfficientNet-B0'},
    'staff':  {'target_acc': 95.1, 'architecture': 'ResNet-34'},
}


def log(msg: str) -> None:
    """Print a log line — will appear in job['logs'] on the backend."""
    print(f'LOG {msg}', flush=True)


def metric(epoch: int, train_acc: float, val_acc: float,
           train_loss: float, val_loss: float) -> None:
    """Print a metric line — parsed by the script runner into job['metrics']."""
    print(
        f'METRIC {epoch} '
        f'{round(train_acc, 2)} {round(val_acc, 2)} '
        f'{round(train_loss, 4)} {round(val_loss, 4)}',
        flush=True,
    )


def done(final_val_acc: float) -> None:
    """Print the final result line."""
    print(f'DONE {round(final_val_acc, 2)}', flush=True)


def error(msg: str) -> None:
    """Print an error line and exit with code 1."""
    print(f'ERROR {msg}', flush=True)
    sys.exit(1)


def simulate_epoch(epoch: int, total_epochs: int, target_acc: float) -> tuple:
    """
    Simulate one training epoch.
    Replace this function with real training code.
    Returns: (train_acc, val_acc, train_loss, val_loss)
    """
    progress   = epoch / total_epochs
    noise      = lambda: (random.random() - 0.5) * 2.0
    train_acc  = min(99.0, target_acc * 0.85 * progress + 40 * (1 - progress) + noise())
    val_acc    = min(99.0, target_acc * progress         + 35 * (1 - progress) + noise())
    train_loss = max(0.01, 1.8  * (1 - progress * 0.90) + noise() * 0.05)
    val_loss   = max(0.05, 2.1  * (1 - progress * 0.85) + noise() * 0.08)
    return train_acc, val_acc, train_loss, val_loss


def main():
    parser = argparse.ArgumentParser(description='OLY VISION dummy training script')
    parser.add_argument('--model',     required=True, help='Model type: gender | age | staff')
    parser.add_argument('--epochs',    type=int, default=20, help='Number of epochs')
    parser.add_argument('--data-dir',  default='./data', help='Path to dataset directory')
    parser.add_argument('--threshold', type=float, default=90.0, help='Accuracy threshold for deployment')
    args = parser.parse_args()

    if args.model not in DUMMY_CONFIG:
        error(f'Unknown model "{args.model}". Choose from: {list(DUMMY_CONFIG)}')

    cfg = DUMMY_CONFIG[args.model]

    log(f'Starting {args.model} training')
    log(f'Architecture: {cfg["architecture"]}')
    log(f'Dataset path: {args.data_dir}')
    log(f'Epochs: {args.epochs}')
    log(f'Threshold: {args.threshold}%')

    final_val_acc = 0.0

    for epoch in range(1, args.epochs + 1):
        time.sleep(0.05)  # simulate compute time — reduce for faster testing

        train_acc, val_acc, train_loss, val_loss = simulate_epoch(
            epoch, args.epochs, cfg['target_acc']
        )
        final_val_acc = val_acc
        metric(epoch, train_acc, val_acc, train_loss, val_loss)

    done(final_val_acc)


if __name__ == '__main__':
    main()
