"""
Mock training script — placeholder until Thiyagu shares the real scripts.

Usage:
    python scripts/mock_training.py --model gender --epochs 20

This script prints metrics in the format the training service expects.
Replace this with the real training code when available.
"""
import argparse
import time
import random
import math

MODEL_CONFIG = {
    'gender': {'target_acc': 92.4, 'architecture': 'ResNet-50'},
    'age':    {'target_acc': 87.3, 'architecture': 'EfficientNet-B0'},
    'staff':  {'target_acc': 95.1, 'architecture': 'ResNet-34'},
}


def train(model: str, epochs: int = 20):
    cfg = MODEL_CONFIG.get(model)
    if not cfg:
        print(f'ERROR: unknown model "{model}". Choose: {list(MODEL_CONFIG)}')
        return

    print(f'[INFO] Starting {model} training')
    print(f'[INFO] Architecture: {cfg["architecture"]}')
    print(f'[INFO] Epochs: {epochs}')

    for epoch in range(1, epochs + 1):
        time.sleep(0.1)  # simulate compute

        progress   = epoch / epochs
        noise      = lambda: (random.random() - 0.5) * 2
        target     = cfg['target_acc']
        train_acc  = min(99, target * 0.85 * progress + 40 * (1 - progress) + noise())
        val_acc    = min(99, target * progress         + 35 * (1 - progress) + noise())
        train_loss = max(0.01, 1.8  * (1 - progress * 0.90) + noise() * 0.05)
        val_loss   = max(0.05, 2.1  * (1 - progress * 0.85) + noise() * 0.08)

        # Output format: METRIC epoch train_acc val_acc train_loss val_loss
        print(
            f'METRIC {epoch} '
            f'{round(train_acc,2)} {round(val_acc,2)} '
            f'{round(train_loss,4)} {round(val_loss,4)}'
        )

    print(f'[DONE] Training complete. Final val_acc: {round(val_acc,2)}%')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mock training script')
    parser.add_argument('--model',  default='gender', help='Model to train')
    parser.add_argument('--epochs', default=20, type=int, help='Number of epochs')
    args = parser.parse_args()
    train(args.model, args.epochs)
