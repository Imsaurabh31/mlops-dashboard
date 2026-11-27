import torch
import os
import copy

from tqdm.auto import tqdm
from typing import Dict, List, Tuple, Optional, Any
from torchmetrics import F1Score, Accuracy, Precision, Recall

def train_step(model: torch.nn.Module,
               dataloader: torch.utils.data.DataLoader,
               loss_fn: torch.nn.Module,
               optimizer: torch.optim.Optimizer,
               device: torch.device) -> Tuple[float, float]:
    """Trains a PyTorch model for a single epoch.

    Turns a target PyTorch model to training mode and then
    runs through all of the required training steps (forward
    pass, loss calculation, optimizer step).

    Args:
        model: A PyTorch model to be trained.
        dataloader: A DataLoader instance for the model to be trained on.
        loss_fn: A PyTorch loss function to minimize.
        optimizer: A PyTorch optimizer to help minimize the loss function.
        device: A target device to compute on (e.g. "cuda" or "cpu").

    Returns:
        A tuple of training loss and training accuracy metrics.
        In the form (train_loss, train_accuracy). For example:

        (0.1112, 0.8743)
    """
    # Put model in train mode
    model.train()

    # Setup train loss and train accuracy values
    train_loss, train_acc = 0, 0

    # Loop through data loader data batches
    for batch, (X, y) in enumerate(dataloader):
        # Send data to target device
        X, y = X.to(device), y.to(device)

        # 1. Forward pass
        y_pred = model(X)

        # 2. Calculate and accumulate loss
        loss = loss_fn(y_pred, y)
        train_loss += loss.item()

        # 3. Optimizer zero grad
        optimizer.zero_grad()

        # 4. Loss backward
        loss.backward()

        # 5. Optimizer step
        optimizer.step()

        # Calculate and accumulate accuracy metric across all batches
        y_pred_class = torch.argmax(torch.softmax(y_pred, dim=1), dim=1)
        train_acc += (y_pred_class == y).sum().item()/len(y_pred)

    # Adjust metrics to get average loss and accuracy per batch
    train_loss = train_loss / len(dataloader)
    train_acc = train_acc / len(dataloader)
    return train_loss, train_acc

def test_step(model: torch.nn.Module,
              dataloader: torch.utils.data.DataLoader,
              loss_fn: torch.nn.Module,
              device: torch.device) -> Tuple[float, float]:
    """Tests a PyTorch model for a single epoch.

    Turns a target PyTorch model to "eval" mode and then performs
    a forward pass on a testing dataset.

    Args:
        model: A PyTorch model to be tested.
        dataloader: A DataLoader instance for the model to be tested on.
        loss_fn: A PyTorch loss function to calculate loss on the test data.
        device: A target device to compute on (e.g. "cuda" or "cpu").

    Returns:
        A tuple of testing loss and testing accuracy metrics.
        In the form (test_loss, test_accuracy). For example:

        (0.0223, 0.8985)
    """
    # Put model in eval mode
    model.eval()

    # Setup test loss and test accuracy values
    test_loss, test_acc = 0, 0

    # Turn on inference context manager
    with torch.inference_mode():
        # Loop through DataLoader batches
        for batch, (X, y) in enumerate(dataloader):
            # Send data to target device
            X, y = X.to(device), y.to(device)

            # 1. Forward pass
            test_pred_logits = model(X)

            # 2. Calculate and accumulate loss
            loss = loss_fn(test_pred_logits, y)
            test_loss += loss.item()

            # Calculate and accumulate accuracy
            test_pred_labels = test_pred_logits.argmax(dim=1)
            test_acc += ((test_pred_labels == y).sum().item()/len(test_pred_labels))

    # Adjust metrics to get average loss and accuracy per batch
    test_loss = test_loss / len(dataloader)
    test_acc = test_acc / len(dataloader)
    return test_loss, test_acc

def save_model(model, epoch, save_dir="/kaggle/working/model"):
    os.makedirs(save_dir, exist_ok=True)
    model_filename = f"model_epoch_{epoch}.pt"
    model_path = os.path.join(save_dir, model_filename)
    torch.save(model.state_dict(), model_path)

def train(model: torch.nn.Module,
          train_dataloader: torch.utils.data.DataLoader,
          test_dataloader: torch.utils.data.DataLoader,
          optimizer: torch.optim.Optimizer,
          loss_fn: torch.nn.Module,
          epochs: int,
          device: torch.device,
          save_dir="/kaggle/working/model"):  # Specify the directory where you want to save the models
    """Trains and tests a PyTorch model."""
    results = {"train_loss": [],
               "train_acc": [],
               "test_loss": [],
               "test_acc": []
              }

    # Create the save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    # Open a text file for writing the results
    with open(os.path.join(save_dir, "training_results.txt"), "w") as results_file:
        for epoch in tqdm(range(epochs)):
            train_loss, train_acc = train_step(model=model, dataloader=train_dataloader, loss_fn=loss_fn, optimizer=optimizer, device=device)
            test_loss, test_acc = test_step(model=model, dataloader=test_dataloader, loss_fn=loss_fn, device=device)

            # Print metrics
            print(
                f"Epoch: {epoch+1} | "
                f"train_loss: {train_loss:.4f} | "
                f"train_acc: {train_acc:.4f} | "
                f"test_loss: {test_loss:.4f} | "
                f"test_acc: {test_acc:.4f}"
            )

            # Write metrics to the results file
            results_file.write(
                f"Epoch: {epoch+1} | "
                f"train_loss: {train_loss:.4f} | "
                f"train_acc: {train_acc:.4f} | "
                f"test_loss: {test_loss:.4f} | "
                f"test_acc: {test_acc:.4f}\n"
            )

            results["train_loss"].append(train_loss)
            results["train_acc"].append(train_acc)
            results["test_loss"].append(test_loss)
            results["test_acc"].append(test_acc)

            # Save the model at the end of each epoch
            save_model(model, epoch + 1, save_dir)  # Save the model in the specified directory

    return results


def _val_with_preds(model, dataloader, loss_fn, device, num_classes):
    """Run a validation pass and also return collected predictions/labels."""
    model.eval()
    val_loss = 0.0
    y_true, y_pred = [], []
    with torch.inference_mode():
        for X, y in dataloader:
            X, y = X.to(device), y.to(device)
            logits = model(X)
            val_loss += loss_fn(logits, y).item()
            preds = logits.argmax(dim=1)
            y_true.append(y.detach().cpu())
            y_pred.append(preds.detach().cpu())
    val_loss /= max(len(dataloader), 1)
    y_true = torch.cat(y_true) if y_true else torch.empty(0, dtype=torch.long)
    y_pred = torch.cat(y_pred) if y_pred else torch.empty(0, dtype=torch.long)
    acc = Accuracy(task='multiclass', num_classes=num_classes)(y_pred, y_true).item() if len(y_true) else 0.0
    f1_macro = F1Score(task='multiclass', num_classes=num_classes, average='macro')(y_pred, y_true).item() if len(y_true) else 0.0
    f1_binary = F1Score(task='multiclass', num_classes=num_classes, average='none')(y_pred, y_true)[1].item() if (len(y_true) and num_classes == 2) else f1_macro
    return val_loss, acc, f1_macro, f1_binary, y_true, y_pred


def train_with_tuning(model: torch.nn.Module,
                      train_dataloader: torch.utils.data.DataLoader,
                      val_dataloader: torch.utils.data.DataLoader,
                      optimizer: torch.optim.Optimizer,
                      loss_fn: torch.nn.Module,
                      epochs: int,
                      device: torch.device,
                      num_classes: int,
                      scheduler: Optional[Any] = None,
                      scheduler_kind: str = 'cosine',
                      patience: int = 5,
                      metric: str = 'f1_macro',
                      save_dir: str = '.',
                      verbose: bool = True) -> Dict[str, Any]:
    """Train with LR scheduler + early stopping; track best checkpoint by val metric.

    metric: 'f1_macro' | 'f1_binary' | 'accuracy'
    scheduler_kind: 'cosine' | 'plateau' | 'none' (controls how .step() is called)
    Returns dict with history, best_epoch, best_metric, best_state_dict, final_metrics.
    """
    os.makedirs(save_dir, exist_ok=True)
    history = {"epoch": [], "train_loss": [], "train_acc": [],
               "val_loss": [], "val_acc": [], "val_f1_macro": [], "val_f1_binary": [], "lr": []}

    best_metric = -float('inf')
    best_epoch = 0
    best_state_dict = copy.deepcopy(model.state_dict())
    epochs_no_improve = 0

    def _select(acc, f1m, f1b):
        if metric == 'accuracy':
            return acc
        if metric == 'f1_binary':
            return f1b
        return f1m

    log_path = os.path.join(save_dir, "training_results.txt")
    with open(log_path, "w") as logf:
        for epoch in range(1, epochs + 1):
            train_loss, train_acc = train_step(model, train_dataloader, loss_fn, optimizer, device)
            val_loss, val_acc, val_f1m, val_f1b, _, _ = _val_with_preds(
                model, val_dataloader, loss_fn, device, num_classes
            )

            current_lr = optimizer.param_groups[0]["lr"]
            history["epoch"].append(epoch)
            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)
            history["val_f1_macro"].append(val_f1m)
            history["val_f1_binary"].append(val_f1b)
            history["lr"].append(current_lr)

            if scheduler is not None:
                if scheduler_kind == 'plateau':
                    scheduler.step(_select(val_acc, val_f1m, val_f1b))
                elif scheduler_kind != 'none':
                    scheduler.step()

            score = _select(val_acc, val_f1m, val_f1b)
            improved = score > best_metric
            if improved:
                best_metric = score
                best_epoch = epoch
                best_state_dict = copy.deepcopy(model.state_dict())
                torch.save(best_state_dict, os.path.join(save_dir, "best.pt"))
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1

            msg = (f"Epoch: {epoch} | lr: {current_lr:.2e} | "
                   f"train_loss: {train_loss:.4f} | train_acc: {train_acc:.4f} | "
                   f"val_loss: {val_loss:.4f} | val_acc: {val_acc:.4f} | "
                   f"val_f1_macro: {val_f1m:.4f} | val_f1_binary: {val_f1b:.4f}"
                   f"{'  <- best' if improved else ''}")
            if verbose:
                print(msg)
            logf.write(msg + "\n")
            logf.flush()

            if patience and epochs_no_improve >= patience:
                stop_msg = f"[INFO] Early stop at epoch {epoch} (no {metric} improvement for {patience} epochs)."
                if verbose:
                    print(stop_msg)
                logf.write(stop_msg + "\n")
                break

    model.load_state_dict(best_state_dict)
    return {
        "history": history,
        "best_epoch": best_epoch,
        "best_metric": best_metric,
        "best_state_dict": best_state_dict,
        "metric_name": metric,
    }
