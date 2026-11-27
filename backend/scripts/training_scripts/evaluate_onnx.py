import os
import argparse
import numpy as np
from PIL import Image
import onnxruntime as ort
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from mlxtend.plotting import plot_confusion_matrix

def preprocess_image(image_path, target_size=(224, 224)):
    # Load image in RGB
    img = Image.open(image_path).convert('RGB')
    
    # 1. Resize shortest edge to 256, maintaining aspect ratio
    w, h = img.size
    if w < h:
        new_w = 256
        new_h = int(h * 256 / w)
    else:
        new_h = 256
        new_w = int(w * 256 / h)
    img = img.resize((new_w, new_h), Image.Resampling.BICUBIC)
    
    # 2. Center crop to target_size (224, 224)
    w, h = img.size
    left = (w - target_size[0]) / 2
    top = (h - target_size[1]) / 2
    right = (w + target_size[0]) / 2
    bottom = (h + target_size[1]) / 2
    img = img.crop((left, top, right, bottom))
    
    # 3. Convert to float numpy array, scale to [0, 1]
    img_data = np.array(img).astype(np.float32) / 255.0
    
    # 4. Normalize with ImageNet mean/std
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_data = (img_data - mean) / std
    
    # 5. Transpose to CHW (Channels, Height, Width) and add batch dimension (1, C, H, W)
    img_data = np.transpose(img_data, (2, 0, 1))
    img_data = np.expand_dims(img_data, axis=0)
    return img_data

def evaluate(model_path, data_dir, save_cm_path):
    print(f"Loading ONNX model from {model_path}...")
    
    # Initialize ONNX Runtime session on GPU if available
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if 'CUDAExecutionProvider' in ort.get_available_providers() else ['CPUExecutionProvider']
    print(f"Using execution providers: {providers}")
    session = ort.InferenceSession(model_path, providers=providers)
    
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    
    # Define class names alphabetically (same as PyTorch ImageFolder)
    class_names = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
    print(f"Found classes: {class_names}")
    
    y_true = []
    y_pred = []
    
    # Iterate through each class folder
    for class_idx, class_name in enumerate(class_names):
        class_path = os.path.join(data_dir, class_name)
        image_names = sorted([f for f in os.listdir(class_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        print(f"Processing {len(image_names)} images in class '{class_name}'...")
        
        for i, name in enumerate(image_names):
            img_path = os.path.join(class_path, name)
            try:
                img_data = preprocess_image(img_path)
                # Run inference
                outputs = session.run([output_name], {input_name: img_data})
                logits = outputs[0]
                pred_idx = int(np.argmax(logits, axis=1)[0])
                
                y_true.append(class_idx)
                y_pred.append(pred_idx)
            except Exception as e:
                print(f"Error processing image {img_path}: {e}")
            
            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(image_names)} images...")
                
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='macro')
    cm = confusion_matrix(y_true, y_pred)
    
    print("\n================ Evaluation Results ================")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision (macro): {precision:.4f}")
    print(f"Recall (macro):    {recall:.4f}")
    print(f"F1-Score (macro):  {f1:.4f}")
    print("\nConfusion Matrix:")
    print(cm)
    print("====================================================\n")
    
    # Plot and save confusion matrix
    print(f"Saving confusion matrix PNG to: {save_cm_path}")
    fig, ax = plot_confusion_matrix(cm, class_names=class_names, figsize=(8, 6))
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(f"ONNX Model Confusion Matrix\nAccuracy: {accuracy:.4f}  F1-Score: {f1:.4f}")
    os.makedirs(os.path.dirname(save_cm_path), exist_ok=True)
    fig.savefig(save_cm_path, bbox_inches='tight')
    plt.close(fig)
    print("Confusion matrix PNG saved successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ONNX model on a dataset folder")
    parser.add_argument("--model", type=str, default="/home/nihit/curated_dataset/models_output/best/best_model.onnx",
                        help="Path to the ONNX model")
    parser.add_argument("--data_dir", type=str, default="/home/nihit/curated_dataset/split_1/valid",
                        help="Path to the validation directory")
    parser.add_argument("--save_cm", type=str, default="/home/nihit/curated_dataset/models_output/best/onnx_confusion_matrix.png",
                        help="Path to save the confusion matrix PNG")
    args = parser.parse_args()
    evaluate(args.model, args.data_dir, args.save_cm)
