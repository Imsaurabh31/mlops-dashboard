import os
import csv
import json
import math
import copy
import torch
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from typing import List, Tuple, Dict, Any
import argparse
import random
import timm
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets
from timeit import default_timer as timer
from torchmetrics import ConfusionMatrix, Accuracy, Precision, Recall, F1Score
from mlxtend.plotting import plot_confusion_matrix
import boto3
from botocore.exceptions import NoCredentialsError

# Import your custom modules
import data_setup
import engine

FIXED_MODEL = "convnext_pico.d1_in1k"
FIXED_IMAGE_SIZE = (224, 224)
DEFAULT_SAVE_DIR = "/home/nihit/dhanush/jwc/landmarkindiastaff/models_output"

def save_plot(fig, save_path, filename):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    # Save the figure
    filepath = os.path.join(save_path, filename)
    fig.savefig(filepath)
    plt.close(fig)

import os
import shutil

def delete_directory(directory_path):
    # Check if the directory exists
    if os.path.exists(directory_path):
        # Delete the directory
        shutil.rmtree(directory_path)

        print(f"[INFO] Deleted cache directory: {directory_path}")
    else:
        print(f"[INFO] Cache directory does not exist: {directory_path}")

def upload_directory_to_s3(local_directory, bucket, s3_directory):
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    
    # Initialize the S3 client
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
    print(f"[INFO] Starting upload of model output to S3 bucket: {bucket}")
    for root, _, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_directory)
            s3_path = os.path.join(s3_directory, relative_path).replace("\\", "/")

            try:
                print(f"[INFO] Uploading {local_path} to s3://{bucket}/{s3_path}")
                s3_client.upload_file(local_path, bucket, s3_path)
                print(f"[INFO] Uploaded {local_path} to s3://{bucket}/{s3_path}")

                # Delete the local file after uploading
                #os.remove(local_path)
                print(f"[INFO] Deleted local file: {local_path}")
            except FileNotFoundError:
                print(f"[ERROR] The file was not found: {local_path}")
            except NoCredentialsError:
                print("[ERROR] Credentials not available.")
    print("[INFO] All files have been uploaded and local copies deleted successfully.")

def find_best_epoch(results_file):
    best_epoch = None
    best_test_loss = float('inf')
    with open(results_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith('Epoch'):
                parts = line.split('|')
                epoch = int(parts[0].split(':')[1].strip())
                test_loss = float(parts[3].split(':')[1].strip())
                if test_loss < best_test_loss:
                    best_test_loss = test_loss
                    best_epoch = epoch
    return best_epoch

def export_best_epoch_model(args, model, model_name):
    # Parse the results file to find the best epoch
    results_file = os.path.join(args.save_dir, model_name, 'training_results.txt')
    best_epoch = find_best_epoch(results_file)
    
    if best_epoch is None:
        print(f"[ERROR] No valid epoch found in {results_file}.")
        return
    
    print(f"[INFO] Best epoch: {best_epoch}")

    # Load the best model checkpoint
    best_model_path = os.path.join(args.save_dir, model_name, f'model_epoch_{best_epoch}.pt')
    if os.path.exists(best_model_path):
        model.load_state_dict(torch.load(best_model_path))
    else:
        print(f"[ERROR] Model checkpoint not found: {best_model_path}")
        return

    model = model.eval().cuda()
    model_export = torch.nn.Sequential(model, torch.nn.Softmax(1))
    x = torch.ones((1, 3, args.image_size[0], args.image_size[1])).cuda()
    export_path = os.path.join(args.save_dir, model_name, f'{model_name}_best_model.onnx')
    torch.onnx.export(model_export, x, export_path, opset_version=14,
                      input_names=['input'],
                      output_names=['output'],
                      dynamic_axes={'input': {0: 'batch_size'},
                                    'output': {0: 'batch_size'}})

    print(f"[INFO] Best model from epoch {best_epoch} has been successfully exported to ONNX format at {export_path}.")



IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def build_train_transform(image_size=FIXED_IMAGE_SIZE):
    h, w = image_size
    return transforms.Compose([
        transforms.Resize(int(h * 256 / 224), interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.RandomResizedCrop(h, scale=(0.7, 1.0), ratio=(0.85, 1.15),
                                     interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.RandAugment(num_ops=2, magnitude=9),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        transforms.RandomErasing(p=0.25, scale=(0.02, 0.2)),
    ])


def build_eval_transform(image_size=FIXED_IMAGE_SIZE):
    h, w = image_size
    return transforms.Compose([
        transforms.Resize(int(h * 256 / 224), interpolation=transforms.InterpolationMode.BICUBIC),
        transforms.CenterCrop(h),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def make_loaders(args, batch_size):
    train_tf = build_train_transform(FIXED_IMAGE_SIZE)
    eval_tf = build_eval_transform(FIXED_IMAGE_SIZE)
    train_set = datasets.ImageFolder(args.train_dir, transform=train_tf)
    val_set = datasets.ImageFolder(args.val_dir, transform=eval_tf)
    test_set = datasets.ImageFolder(args.test_dir, transform=eval_tf)
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True,
                              num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False,
                            num_workers=args.num_workers, pin_memory=True)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False,
                             num_workers=args.num_workers, pin_memory=True)
    return train_loader, val_loader, test_loader, train_set.classes


# =========================================================================
# Optional architectural enhancements (all toggleable; defaults == stock).
#
# The whole block is bypassed unless --head_arch enhanced is passed, so the
# baseline pipeline (stock timm head) is byte-for-byte unchanged by default.
# Every sub-feature is independently switchable so the same script works for
# a new backbone or a new dataset just by flipping flags:
#   --pool_type   avg|gem|attention      (spatial aggregation before the head)
#   --multi_scale                        (fuse stages 2+3+4 instead of last only)
#   --head_type   linear|mlp             (classifier on top of the pooled vector)
#   --head_dropout / --drop_path_rate    (regularization knobs)
#   --head_lr_mult                       (give new layers a higher LR; 2-group)
#   --tta_hflip                          (eval-time horizontal-flip averaging)
# =========================================================================

class GeMPool(nn.Module):
    """Generalized-mean pooling over the spatial grid (learnable exponent p)."""
    def __init__(self, p: float = 3.0, eps: float = 1e-6):
        super().__init__()
        self.p = nn.Parameter(torch.ones(1) * p)
        self.eps = eps

    def forward(self, x):  # x: (B, C, H, W) -> (B, C)
        return x.clamp(min=self.eps).pow(self.p).mean(dim=(2, 3)).pow(1.0 / self.p)


class AvgPool(nn.Module):
    """Plain global average pooling (matches the stock ConvNeXt head)."""
    def forward(self, x):  # (B, C, H, W) -> (B, C)
        return x.mean(dim=(2, 3))


class AttnPool(nn.Module):
    """Single learnable-query attention pooling over the H*W spatial tokens.

    Learns to weight the discriminative cells (head/torso/silhouette) instead
    of averaging them into the background, which plain GAP does.
    """
    def __init__(self, dim: int):
        super().__init__()
        heads = 4 if dim % 4 == 0 else 1
        self.norm = nn.LayerNorm(dim)
        self.query = nn.Parameter(torch.randn(1, 1, dim) * 0.02)
        self.attn = nn.MultiheadAttention(dim, heads, batch_first=True)

    def forward(self, x):  # (B, C, H, W) -> (B, C)
        b, c, h, w = x.shape
        tokens = self.norm(x.flatten(2).transpose(1, 2))   # (B, H*W, C)
        q = self.query.expand(b, -1, -1)                   # (B, 1, C)
        out, _ = self.attn(q, tokens, tokens)              # (B, 1, C)
        return out.squeeze(1)


def _make_pool(pool_type: str, dim: int) -> nn.Module:
    if pool_type == "avg":
        return AvgPool()
    if pool_type == "gem":
        return GeMPool()
    if pool_type == "attention":
        return AttnPool(dim)
    raise ValueError(f"Unknown pool_type: {pool_type}")


def _make_head(head_type: str, in_dim: int, dropout: float, num_classes: int) -> nn.Module:
    if head_type == "linear":
        return nn.Sequential(nn.Dropout(dropout), nn.Linear(in_dim, num_classes))
    if head_type == "mlp":
        return nn.Sequential(
            nn.Linear(in_dim, 256), nn.GELU(), nn.BatchNorm1d(256), nn.Dropout(dropout),
            nn.Linear(256, 128), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )
    raise ValueError(f"Unknown head_type: {head_type}")


class EnhancedClassifier(nn.Module):
    """timm backbone (feature maps) + configurable pooling/fusion/head.

    Submodule named `backbone` so the optimizer can split it from the freshly
    initialized layers for layer-wise LR (see _param_groups).
    """
    def __init__(self, backbone, feat_dims, pool_type, multi_scale,
                 fusion_dim, head_type, head_dropout, num_classes):
        super().__init__()
        self.backbone = backbone
        self.multi_scale = multi_scale
        self.pools = nn.ModuleList(_make_pool(pool_type, d) for d in feat_dims)
        if multi_scale:
            self.projs = nn.ModuleList(nn.Linear(d, fusion_dim) for d in feat_dims)
            head_in = fusion_dim * len(feat_dims)
        else:
            self.projs = None
            head_in = feat_dims[-1]
        self.norm = nn.LayerNorm(head_in)
        self.head = _make_head(head_type, head_in, head_dropout, num_classes)

    def forward(self, x):
        feats = self.backbone(x)                       # list of (B, C, H, W)
        pooled = [pool(f) for pool, f in zip(self.pools, feats)]
        if self.projs is not None:
            pooled = [proj(p) for proj, p in zip(self.projs, pooled)]
            z = torch.cat(pooled, dim=1)
        else:
            z = pooled[-1]
        return self.head(self.norm(z))


def _load_finetune(model, finetune_weights: str):
    if finetune_weights and os.path.isfile(finetune_weights):
        state = torch.load(finetune_weights, map_location="cpu")
        state_dict = state.get("state_dict", state) if isinstance(state, dict) else state
        if not isinstance(state_dict, dict):
            state_dict = state
        load_result = model.load_state_dict(state_dict, strict=False)
        print(f"[INFO] Finetune weights loaded (missing={len(load_result.missing_keys)}, "
              f"unexpected={len(load_result.unexpected_keys)})")
    elif finetune_weights:
        print(f"[WARN] Finetune weights path not found: {finetune_weights}")
    return model


def _timm_create(name, **kwargs):
    """timm.create_model that strips kwargs a given model doesn't accept
    (e.g. RepViT has no drop_path_rate), so any backbone works without edits."""
    try:
        return timm.create_model(name, **kwargs)
    except TypeError as e:
        for bad in ("drop_path_rate", "drop_rate"):
            if bad in kwargs and bad in str(e):
                kwargs.pop(bad)
                print(f"[WARN] {name} does not accept '{bad}'; ignoring it.")
                return _timm_create(name, **kwargs)
        raise


def build_model(args, num_classes: int, pretrained: bool = True):
    """Build stock or enhanced model based on args. Used by both train + export
    so the exported ONNX always matches the trained architecture."""
    # --scratch: random init instead of ImageNet weights (export already passes
    # pretrained=False, so this only changes the training-time starting point).
    pretrained = pretrained and not getattr(args, "scratch", False)
    if getattr(args, "head_arch", "stock") == "stock":
        model = _timm_create(
            FIXED_MODEL, pretrained=pretrained, num_classes=num_classes,
            drop_path_rate=args.drop_path_rate, drop_rate=args.head_dropout,
        )
        return _load_finetune(model, args.finetune_weights)

    # Enhanced: tap stage 4 only, or stages 2+3+4 for multi-scale fusion.
    out_indices = (1, 2, 3) if args.multi_scale else (3,)
    backbone = _timm_create(
        FIXED_MODEL, pretrained=pretrained, features_only=True,
        out_indices=out_indices, drop_path_rate=args.drop_path_rate,
    )
    feat_dims = list(backbone.feature_info.channels())
    model = EnhancedClassifier(
        backbone, feat_dims, args.pool_type, args.multi_scale,
        args.fusion_dim, args.head_type, args.head_dropout, num_classes,
    )
    return _load_finetune(model, args.finetune_weights)


def _param_groups(model, base_lr: float, head_lr_mult: float, head_arch: str):
    """Single group by default; two groups (backbone vs. fresh head) when
    head_lr_mult != 1.0 so newly initialized layers can train faster than the
    pretrained backbone."""
    if head_lr_mult == 1.0:
        return [{"params": [p for p in model.parameters() if p.requires_grad], "lr": base_lr}]
    backbone, head = [], []
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if head_arch == "enhanced":
            is_head = not n.startswith("backbone.")
        else:  # stock convnext: classifier lives under `head.`
            is_head = n.startswith("head.")
        (head if is_head else backbone).append(p)
    groups = [{"params": backbone, "lr": base_lr}]
    if head:
        groups.append({"params": head, "lr": base_lr * head_lr_mult})
    return groups


def build_optimizer(name: str, model, lr: float, head_lr_mult: float = 1.0,
                    head_arch: str = "stock"):
    name = name.lower()
    groups = _param_groups(model, lr, head_lr_mult, head_arch)
    if name == "adamw":
        return torch.optim.AdamW(groups, lr=lr, weight_decay=0.05)
    if name == "sgd":
        return torch.optim.SGD(groups, lr=lr, momentum=0.9,
                               nesterov=True, weight_decay=5e-4)
    raise ValueError(f"Unknown optimizer: {name}")


def build_scheduler(kind: str, optimizer, epochs: int, base_lr: float):
    kind = kind.lower()
    if kind == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=max(epochs, 1), eta_min=base_lr * 0.01
        )
    if kind == "plateau":
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=2
        )
    if kind == "none":
        return None
    raise ValueError(f"Unknown scheduler: {kind}")


def load_fixed_config(path: str, args) -> Dict[str, Any]:
    """Load lr/batch_size/optimizer/epochs from a saved best_config.json.

    The previously-ignored --lr / --batch_size / --epochs flags act as overrides
    here (e.g. extend epochs since the prior best stopped at the cap)."""
    with open(path) as f:
        c = json.load(f)
    missing = [k for k in ("lr", "batch_size", "optimizer", "epochs") if k not in c]
    if missing:
        raise ValueError(f"--config {path} is missing required keys: {missing}")
    cfg = {"lr": float(c["lr"]), "batch_size": int(c["batch_size"]),
           "optimizer": str(c["optimizer"]), "epochs": int(c["epochs"])}
    if args.lr is not None:
        cfg["lr"] = float(args.lr)
    if args.batch_size is not None:
        cfg["batch_size"] = int(args.batch_size)
    if args.epochs is not None:
        cfg["epochs"] = int(args.epochs)
    print(f"[INFO] Loaded fixed config from {path}: {cfg}")
    return cfg


def sample_configs(args) -> List[Dict[str, Any]]:
    # If a saved config is supplied, skip the search and run exactly one trial.
    if getattr(args, "config", ""):
        return [load_fixed_config(args.config, args)]

    rng = random.Random(args.seed)
    configs = []
    if args.search_mode == "grid":
        for lr in args.lr_grid:
            for bs in args.batch_sizes:
                for opt in args.optimizers:
                    for ep in args.epoch_choices:
                        configs.append({"lr": float(lr), "batch_size": int(bs),
                                        "optimizer": opt, "epochs": int(ep)})
    else:  # random
        for _ in range(args.n_trials):
            log_min, log_max = math.log10(args.lr_min), math.log10(args.lr_max)
            lr = 10 ** rng.uniform(log_min, log_max)
            configs.append({
                "lr": lr,
                "batch_size": rng.choice(args.batch_sizes),
                "optimizer": rng.choice(args.optimizers),
                "epochs": rng.choice(args.epoch_choices),
            })
    return configs


def evaluate_loader(model, loader, device, num_classes, tta_hflip: bool = False):
    """Evaluate on a loader. With tta_hflip, average softmax probabilities over
    the image and its horizontal flip (eval-only; NOT baked into the ONNX)."""
    model.eval()
    y_true, y_pred = [], []
    with torch.inference_mode():
        for X, y in loader:
            X = X.to(device)
            if tta_hflip:
                probs = torch.softmax(model(X), dim=1)
                probs = probs + torch.softmax(model(torch.flip(X, dims=[3])), dim=1)
                y_pred.append(probs.argmax(dim=1).cpu())
            else:
                y_pred.append(model(X).argmax(dim=1).cpu())
            y_true.append(y.cpu())
    y_true = torch.cat(y_true) if y_true else torch.empty(0, dtype=torch.long)
    y_pred = torch.cat(y_pred) if y_pred else torch.empty(0, dtype=torch.long)
    confmat = ConfusionMatrix(task="multiclass", num_classes=num_classes)(y_pred, y_true)
    acc = Accuracy(task="multiclass", num_classes=num_classes)(y_pred, y_true).item()
    prec = Precision(task="multiclass", num_classes=num_classes, average="macro")(y_pred, y_true).item()
    rec = Recall(task="multiclass", num_classes=num_classes, average="macro")(y_pred, y_true).item()
    f1m = F1Score(task="multiclass", num_classes=num_classes, average="macro")(y_pred, y_true).item()
    f1b = F1Score(task="multiclass", num_classes=num_classes, average="none")(y_pred, y_true)[1].item() \
        if num_classes == 2 else f1m
    return {
        "accuracy": acc, "precision_macro": prec, "recall_macro": rec,
        "f1_macro": f1m, "f1_binary_pos": f1b,
        "confmat": confmat.cpu().numpy().tolist(),
        "y_true": y_true.tolist(), "y_pred": y_pred.tolist(),
    }


def save_confusion_matrix_png(confmat_list, class_names, title, out_path):
    cm = np.array(confmat_list)
    fig, ax = plot_confusion_matrix(cm, class_names=class_names, figsize=(8, 6))
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(title)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def save_training_curve_png(history: Dict[str, List[float]], out_path: str):
    epochs = history["epoch"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(epochs, history["train_loss"], label="train_loss")
    axes[0].plot(epochs, history["val_loss"], label="val_loss")
    axes[0].set_xlabel("epoch"); axes[0].set_ylabel("loss"); axes[0].legend(); axes[0].set_title("Loss")
    axes[1].plot(epochs, history["val_f1_macro"], label="val_f1_macro")
    axes[1].plot(epochs, history["val_acc"], label="val_acc")
    axes[1].set_xlabel("epoch"); axes[1].set_ylabel("metric"); axes[1].legend(); axes[1].set_title("Val metrics")
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def run_trial(args, trial_id: int, hp: Dict[str, Any], device: str) -> Dict[str, Any]:
    trial_dir = os.path.join(args.save_dir, "trials", f"trial_{trial_id:02d}")
    os.makedirs(trial_dir, exist_ok=True)
    print(f"\n=== Trial {trial_id:02d}: {hp} ===")

    train_loader, val_loader, test_loader, class_names = make_loaders(args, hp["batch_size"])
    num_classes = len(class_names)

    model = build_model(args, num_classes).to(device)
    optimizer = build_optimizer(hp["optimizer"], model, hp["lr"],
                                head_lr_mult=args.head_lr_mult, head_arch=args.head_arch)
    scheduler = build_scheduler(args.scheduler, optimizer, hp["epochs"], hp["lr"])
    loss_fn = nn.CrossEntropyLoss()

    t0 = timer()
    result = engine.train_with_tuning(
        model=model,
        train_dataloader=train_loader,
        val_dataloader=val_loader,
        optimizer=optimizer,
        loss_fn=loss_fn,
        epochs=hp["epochs"],
        device=device,
        num_classes=num_classes,
        scheduler=scheduler,
        scheduler_kind=args.scheduler,
        patience=args.patience,
        metric=args.metric,
        save_dir=trial_dir,
        verbose=True,
    )
    train_time = timer() - t0

    test_metrics = evaluate_loader(model, test_loader, device, num_classes,
                                   tta_hflip=args.tta_hflip)

    # Per-trial artifacts
    save_training_curve_png(result["history"], os.path.join(trial_dir, "training_curve.png"))
    save_confusion_matrix_png(
        test_metrics["confmat"], class_names,
        f"Trial {trial_id:02d}  acc={test_metrics['accuracy']:.3f}  f1_macro={test_metrics['f1_macro']:.3f}",
        os.path.join(trial_dir, "confusion_matrix.png"),
    )
    with open(os.path.join(trial_dir, "config.json"), "w") as f:
        json.dump({**hp, "trial_id": trial_id, "scheduler": args.scheduler,
                   "metric": args.metric, "patience": args.patience}, f, indent=2)
    with open(os.path.join(trial_dir, "history.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        keys = list(result["history"].keys())
        writer.writerow(keys)
        for row in zip(*[result["history"][k] for k in keys]):
            writer.writerow(row)

    return {
        "trial_id": trial_id,
        "hp": hp,
        "best_epoch": result["best_epoch"],
        "val_metric": result["best_metric"],
        "val_metric_name": result["metric_name"],
        "test_metrics": {k: v for k, v in test_metrics.items() if k not in ("y_true", "y_pred")},
        "ckpt_path": os.path.join(trial_dir, "best.pt"),
        "trial_dir": trial_dir,
        "train_time_s": train_time,
        "history": result["history"],
        "class_names": class_names,
        "confmat": test_metrics["confmat"],
    }


def write_tuning_results(args, trials: List[Dict[str, Any]]):
    csv_path = os.path.join(args.save_dir, "tuning_results.csv")
    json_path = os.path.join(args.save_dir, "tuning_results.json")
    fieldnames = ["trial_id", "lr", "batch_size", "optimizer", "epochs_cap",
                  "best_epoch", "val_metric", "val_metric_name",
                  "test_accuracy", "test_precision_macro", "test_recall_macro",
                  "test_f1_macro", "test_f1_binary_pos", "train_time_s"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in trials:
            w.writerow({
                "trial_id": t["trial_id"],
                "lr": t["hp"]["lr"],
                "batch_size": t["hp"]["batch_size"],
                "optimizer": t["hp"]["optimizer"],
                "epochs_cap": t["hp"]["epochs"],
                "best_epoch": t["best_epoch"],
                "val_metric": t["val_metric"],
                "val_metric_name": t["val_metric_name"],
                "test_accuracy": t["test_metrics"]["accuracy"],
                "test_precision_macro": t["test_metrics"]["precision_macro"],
                "test_recall_macro": t["test_metrics"]["recall_macro"],
                "test_f1_macro": t["test_metrics"]["f1_macro"],
                "test_f1_binary_pos": t["test_metrics"]["f1_binary_pos"],
                "train_time_s": round(t["train_time_s"], 2),
            })
    with open(json_path, "w") as f:
        serializable = []
        for t in trials:
            tt = {k: v for k, v in t.items() if k not in ("history", "confmat")}
            tt["history"] = t["history"]
            tt["confmat"] = t["confmat"]
            serializable.append(tt)
        json.dump(serializable, f, indent=2)
    print(f"[INFO] Wrote {csv_path} and {json_path}")


def export_onnx(args, state_dict, num_classes: int, out_path: str, image_size=FIXED_IMAGE_SIZE):
    # Rebuild the exact trained architecture (stock or enhanced) so the ONNX
    # graph matches the checkpoint. TTA is eval-only and intentionally NOT baked in.
    model = build_model(args, num_classes, pretrained=False)
    model.load_state_dict(state_dict)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.eval().to(device)
    model_export = nn.Sequential(model, nn.Softmax(1))
    x = torch.ones((2, 3, image_size[0], image_size[1]), device=device)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    export_kwargs = dict(
        opset_version=14,
        input_names=["input"], output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    )
    # Force the legacy TorchScript exporter: it honors dynamic_axes at opset 14.
    # The newer dynamo exporter (default in torch>=2.x) bakes the batch dim into
    # reshape ops (e.g. attention pooling), breaking dynamic-batch inference.
    try:
        torch.onnx.export(model_export, x, out_path, dynamo=False, **export_kwargs)
    except TypeError:
        torch.onnx.export(model_export, x, out_path, **export_kwargs)  # older torch
    print(f"[INFO] ONNX exported: {out_path}")


def save_best_artifacts(args, best_trial: Dict[str, Any]):
    best_dir = os.path.join(args.save_dir, "best")
    os.makedirs(best_dir, exist_ok=True)
    state_dict = torch.load(best_trial["ckpt_path"], map_location="cpu")
    torch.save(state_dict, os.path.join(best_dir, "best_model.pt"))
    with open(os.path.join(best_dir, "best_config.json"), "w") as f:
        json.dump({
            "model": FIXED_MODEL,
            "image_size": list(FIXED_IMAGE_SIZE),
            "trial_id": best_trial["trial_id"],
            **best_trial["hp"],
            "best_epoch": best_trial["best_epoch"],
            "val_metric_name": best_trial["val_metric_name"],
            "val_metric": best_trial["val_metric"],
            "head_arch": args.head_arch,
            "pool_type": args.pool_type,
            "multi_scale": args.multi_scale,
            "fusion_dim": args.fusion_dim,
            "head_type": args.head_type,
            "head_dropout": args.head_dropout,
            "drop_path_rate": args.drop_path_rate,
            "head_lr_mult": args.head_lr_mult,
            "tta_hflip": args.tta_hflip,
            "scratch": args.scratch,
        }, f, indent=2)
    with open(os.path.join(best_dir, "metrics.json"), "w") as f:
        json.dump(best_trial["test_metrics"], f, indent=2)
    save_training_curve_png(best_trial["history"], os.path.join(best_dir, "training_curve.png"))
    save_confusion_matrix_png(
        best_trial["confmat"], best_trial["class_names"],
        f"BEST  acc={best_trial['test_metrics']['accuracy']:.3f}  "
        f"f1_macro={best_trial['test_metrics']['f1_macro']:.3f}",
        os.path.join(best_dir, "confusion_matrix.png"),
    )
    export_onnx(args, state_dict, len(best_trial["class_names"]),
                os.path.join(best_dir, "best_model.onnx"))


def main(args):
    # Backbone is selectable via --backbone; everything downstream reads the
    # FIXED_MODEL global (build_model, export, artifact records), so set it here.
    global FIXED_MODEL
    if args.backbone:
        FIXED_MODEL = args.backbone
    args.models = [FIXED_MODEL]
    if tuple(args.image_size) != FIXED_IMAGE_SIZE:
        print(f"[WARN] --image_size overridden to {list(FIXED_IMAGE_SIZE)} per task spec.")
    args.image_size = list(FIXED_IMAGE_SIZE)

    if args.val_dir == args.test_dir:
        print("[WARN] val_dir == test_dir; reported test metrics are NOT held-out.")

    set_seed(args.seed)
    os.makedirs(args.save_dir, exist_ok=True)

    if args.scratch and args.finetune_weights:
        raise SystemExit("[ERROR] --scratch and --finetune_weights are mutually exclusive.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Device: {device}")
    print(f"[INFO] Model:  {FIXED_MODEL}  image_size={FIXED_IMAGE_SIZE}  "
          f"weights={'SCRATCH (random init)' if args.scratch else 'ImageNet-pretrained'}")
    if args.head_arch == "enhanced":
        print(f"[INFO] Head:   ENHANCED  pool={args.pool_type}  multi_scale={args.multi_scale}"
              f"  fusion_dim={args.fusion_dim}  head_type={args.head_type}"
              f"  head_dropout={args.head_dropout}  drop_path={args.drop_path_rate}"
              f"  head_lr_mult={args.head_lr_mult}")
    else:
        print(f"[INFO] Head:   stock (drop_path={args.drop_path_rate}, "
              f"head_dropout={args.head_dropout})")
    if args.tta_hflip:
        print("[INFO] TTA:    horizontal-flip averaging at eval (NOT baked into ONNX)")
    print(f"[INFO] Search: {args.search_mode}  n_trials={args.n_trials}  metric={args.metric}")

    configs = sample_configs(args)
    print(f"[INFO] Will run {len(configs)} trial(s).")

    trials = []
    for i, hp in enumerate(configs):
        trial = run_trial(args, i, hp, device)
        trials.append(trial)
        write_tuning_results(args, trials)  # incremental write

    if not trials:
        print("[ERROR] No trials produced.")
        return

    best_trial = max(trials, key=lambda t: (t["val_metric"], t["test_metrics"]["f1_macro"],
                                            -t["hp"]["epochs"], -t["hp"]["lr"]))
    save_best_artifacts(args, best_trial)

    print("\n=== BEST CONFIG ===")
    print(f"trial_id={best_trial['trial_id']}  "
          f"lr={best_trial['hp']['lr']:.2e}  bs={best_trial['hp']['batch_size']}  "
          f"opt={best_trial['hp']['optimizer']}  epochs_cap={best_trial['hp']['epochs']}  "
          f"best_epoch={best_trial['best_epoch']}")
    tm = best_trial["test_metrics"]
    print(f"val_{best_trial['val_metric_name']}={best_trial['val_metric']:.4f}  "
          f"test_f1_macro={tm['f1_macro']:.4f}  test_f1_binary={tm['f1_binary_pos']:.4f}  "
          f"test_acc={tm['accuracy']:.4f}  test_prec={tm['precision_macro']:.4f}  "
          f"test_rec={tm['recall_macro']:.4f}")
    print(f"Saved to: {os.path.join(args.save_dir, 'best')}")

    delete_directory(os.path.expanduser(f"~/.cache/huggingface/hub/models--timm--{FIXED_MODEL.split('.')[0]}"))




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"HP search for binary image classification with {FIXED_MODEL} @ 224.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Data paths
    parser.add_argument("--train_dir", type=str,
                        default="/home/nihit/dhanush/jwc/landmarkindiastaff/split_1/train")
    parser.add_argument("--val_dir", type=str,
                        default="/home/nihit/dhanush/jwc/landmarkindiastaff/split_1/valid")
    parser.add_argument("--test_dir", type=str,
                        default="/home/nihit/dhanush/jwc/landmarkindiastaff/split_1/valid")
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--save_dir", type=str, default=DEFAULT_SAVE_DIR)
    parser.add_argument("--finetune_weights", type=str, default="")
    parser.add_argument("--scratch", action="store_true",
                        help="Train from random initialization instead of ImageNet-pretrained "
                             "weights (applies to the backbone; the head is always fresh). "
                             "Incompatible with --finetune_weights.")

    # Backbone (any timm model name; defaults to the module FIXED_MODEL)
    parser.add_argument("--backbone", type=str, default=FIXED_MODEL,
                        help="timm backbone name, e.g. tiny_vit_5m_224.dist_in22k_ft_in1k, "
                             "convnextv2_pico.fcmae_ft_in1k, repvit_m1.dist_in1k. "
                             "Works in both stock and enhanced head modes.")

    # Search
    parser.add_argument("--config", type=str, default="",
                        help="Path to a saved best_config.json. If set, SKIPS the HP "
                             "search and runs ONE trial using its lr/batch_size/optimizer/"
                             "epochs. --lr/--batch_size/--epochs override individual values; "
                             "architecture flags (--head_arch etc.) still come from the CLI.")
    parser.add_argument("--search_mode", type=str, choices=["random", "grid"], default="random")
    parser.add_argument("--n_trials", type=int, default=12)
    parser.add_argument("--lr_min", type=float, default=1e-5)
    parser.add_argument("--lr_max", type=float, default=1e-3)
    parser.add_argument("--lr_grid", nargs="+", type=float, default=[1e-5, 1e-4, 1e-3],
                        help="Only used when --search_mode grid.")
    parser.add_argument("--batch_sizes", nargs="+", type=int, default=[16, 32, 64])
    parser.add_argument("--optimizers", nargs="+", type=str, default=["AdamW", "SGD"],
                        choices=["AdamW", "SGD"])
    parser.add_argument("--epoch_choices", nargs="+", type=int, default=[15, 25, 40])

    # Training behavior
    parser.add_argument("--patience", type=int, default=5,
                        help="Early stop after N epochs with no val-metric improvement.")
    parser.add_argument("--scheduler", type=str, choices=["cosine", "plateau", "none"], default="cosine")
    parser.add_argument("--metric", type=str, choices=["f1_macro", "f1_binary", "accuracy"],
                        default="f1_macro")
    parser.add_argument("--seed", type=int, default=42)

    # ---- Architecture enhancements (all default to stock behavior) ----
    # Master switch: 'stock' = unchanged baseline; 'enhanced' = custom pool/fusion/head.
    parser.add_argument("--head_arch", type=str, choices=["stock", "enhanced"], default="stock",
                        help="'enhanced' activates --pool_type/--multi_scale/--head_type.")
    parser.add_argument("--pool_type", type=str, choices=["avg", "gem", "attention"], default="avg",
                        help="Spatial pooling before the head (enhanced only).")
    parser.add_argument("--multi_scale", action="store_true",
                        help="Fuse stages 2+3+4 instead of last stage only (enhanced only).")
    parser.add_argument("--fusion_dim", type=int, default=128,
                        help="Per-stage projection width for multi-scale fusion.")
    parser.add_argument("--head_type", type=str, choices=["linear", "mlp"], default="linear",
                        help="Classifier head (enhanced only).")
    parser.add_argument("--head_dropout", type=float, default=0.0,
                        help="Dropout in the classifier head (works for stock + enhanced).")
    parser.add_argument("--drop_path_rate", type=float, default=0.0,
                        help="Stochastic depth in the backbone (works for stock + enhanced).")
    parser.add_argument("--head_lr_mult", type=float, default=1.0,
                        help=">1.0 trains fresh head/pool layers faster than the backbone "
                             "(two param groups). 1.0 = single group (default).")
    parser.add_argument("--tta_hflip", action="store_true",
                        help="Average over horizontal flip at eval time (not in ONNX).")

    # Backwards-compatible (ignored by the search loop but still parsed)
    parser.add_argument("--lr", type=float, default=None, help="(ignored; search owns LR)")
    parser.add_argument("--epochs", type=int, default=None, help="(ignored; search owns epochs)")
    parser.add_argument("--batch_size", type=int, default=None, help="(ignored; search owns batch_size)")
    parser.add_argument("--dropout", type=float, default=None, help="(ignored)")
    parser.add_argument("--image_size", nargs=2, type=int, default=list(FIXED_IMAGE_SIZE),
                        help=f"(forced to {list(FIXED_IMAGE_SIZE)})")
    parser.add_argument("--models", nargs="+", type=str, default=[FIXED_MODEL],
                        help=f"(forced to [{FIXED_MODEL}])")

    args = parser.parse_args()
    # Under --config, lr/epochs/batch_size act as overrides (handled in
    # load_fixed_config); only warn that they're ignored in HP-search mode.
    ignored = ("dropout",) if args.config else ("lr", "epochs", "batch_size", "dropout")
    for k in ignored:
        if getattr(args, k) is not None:
            print(f"[INFO] --{k} is ignored under HP search; controlled by --lr_min/--lr_max, "
                  f"--epoch_choices, --batch_sizes.")
    main(args)
