"""
YOLOv8 Training Script for Chili Disease Detection
Optimized for deployment on Raspberry Pi 4
"""

from ultralytics import YOLO
import torch
import os
from datetime import datetime

def main():
    # Check available device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"=" * 60)
    print(f"Training on: {device}")
    if device == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"=" * 60)
    
    # Load YOLOv8 nano model (smallest, best for Raspberry Pi)
    print("\nLoading YOLOv8n model...")
    model = YOLO('yolov8n.pt')
    
    # Training configuration optimized for Raspberry Pi deployment
    print("\nStarting training...")
    print("Configuration:")
    print(f"  - Model: YOLOv8n (nano)")
    print(f"  - Image size: 416x416")
    print(f"  - Epochs: 100")
    print(f"  - Batch size: {'16' if device == 'cuda' else '4'}")
    print(f"  - Classes: antraknosa, cabai_normal, lalat_buah")
    print(f"=" * 60)
    
    results = model.train(
        # Data
        data='data/data.yaml',
        
        # Training parameters
        epochs=100,
        imgsz=416,  # Smaller size for Raspberry Pi (320, 416, or 640)
        batch=16 if device == 'cuda' else 4,  # Adjust based on GPU/CPU
        device=device,
        
        # Optimization
        workers=8 if device == 'cuda' else 4,  # Number of data loading workers
        cache=False,  # Cache images to RAM for faster training
        amp=True if device == 'cuda' else False,  # Automatic Mixed Precision for GPU
        
        # Output
        project='runs/train',
        name=f'chili_disease_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        exist_ok=True,
        
        # Early stopping and saving
        patience=20,  # Stop if no improvement for 20 epochs
        save=True,
        save_period=10,  # Save checkpoint every 10 epochs
        
        # Visualization
        plots=True,
        
        # Augmentation (default is good for most cases)
        hsv_h=0.015,  # Image HSV-Hue augmentation
        hsv_s=0.7,    # Image HSV-Saturation augmentation
        hsv_v=0.4,    # Image HSV-Value augmentation
        degrees=0.0,  # Image rotation
        translate=0.1,  # Image translation
        scale=0.5,    # Image scale
        fliplr=0.5,   # Horizontal flip probability
    )
    
    print("\n" + "=" * 60)
    print("Training completed!")
    print(f"Best model saved at: {results.save_dir}/weights/best.pt")
    print(f"Last model saved at: {results.save_dir}/weights/last.pt")
    print("\nTraining metrics:")
    print(f"  - Final mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"  - Final mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")
    print("=" * 60)
    
    # Validate the best model
    print("\nValidating best model...")
    best_model = YOLO(f"{results.save_dir}/weights/best.pt")
    val_results = best_model.val(data='data/data.yaml', imgsz=416)
    
    print("\nValidation Results:")
    print(f"  - mAP50: {val_results.box.map50:.4f}")
    print(f"  - mAP50-95: {val_results.box.map:.4f}")
    print(f"  - Precision: {val_results.box.mp:.4f}")
    print(f"  - Recall: {val_results.box.mr:.4f}")
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("1. Review training plots in:", results.save_dir)
    print("2. Export model for Raspberry Pi: python export_for_pi.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
