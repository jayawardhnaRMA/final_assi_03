"""
Export YOLOv8 Model for Raspberry Pi 4
Converts trained model to TensorFlow Lite INT8 format for optimal performance
"""

from ultralytics import YOLO
import os
import glob

def find_best_model():
    """Find the most recent best.pt model in runs/train"""
    train_runs = glob.glob('runs/train/*/weights/best.pt')
    
    if not train_runs:
        print("ERROR: No trained model found!")
        print("Please train a model first using: python train.py")
        return None
    
    # Get the most recent model
    latest_model = max(train_runs, key=os.path.getctime)
    return latest_model

def export_to_tflite(model_path, output_name='chili_disease_pi'):
    """Export model to TFLite INT8 format"""
    
    print("=" * 60)
    print("Exporting YOLOv8 Model for Raspberry Pi 4")
    print("=" * 60)
    print(f"\nInput model: {model_path}")
    
    # Load the trained model
    model = YOLO(model_path)
    
    # Export to TFLite with INT8 quantization
    print("\nExporting to TensorFlow Lite (INT8)...")
    print("This will optimize the model for Raspberry Pi performance")
    print("(This may take a few minutes...)")
    
    export_path = model.export(
        format='tflite',
        imgsz=416,  # Must match training size
        int8=True,  # INT8 quantization for 4x speed boost
        data='data/data.yaml',  # Required for calibration
    )
    
    print("\n" + "=" * 60)
    print("Export completed successfully!")
    print(f"Model saved at: {export_path}")
    
    # Get model size
    model_size_mb = os.path.getsize(export_path) / (1024 * 1024)
    print(f"Model size: {model_size_mb:.2f} MB")
    
    print("\n" + "=" * 60)
    print("Raspberry Pi Deployment Instructions:")
    print("=" * 60)
    print("\n1. Transfer the model to your Raspberry Pi:")
    print(f"   scp {export_path} pi@raspberrypi.local:~/")
    
    print("\n2. Install required packages on Raspberry Pi:")
    print("   pip install ultralytics opencv-python")
    
    print("\n3. Use the model for inference (see inference_pi.py)")
    
    print("\n" + "=" * 60)
    print("Expected Performance on Raspberry Pi 4:")
    print("  - FPS: 10-15 (with INT8 optimization)")
    print("  - Resolution: 416x416")
    print("  - Use cases: Plant disease monitoring, periodic scans")
    print("\nFor real-time video (25-30 FPS):")
    print("  - Consider Google Coral USB Accelerator")
    print("=" * 60)
    
    return export_path

def main():
    # Find the best trained model
    model_path = find_best_model()
    
    if model_path is None:
        return
    
    print(f"\nFound trained model: {model_path}")
    
    # Ask user to confirm
    response = input("\nProceed with export? (y/n): ").strip().lower()
    if response != 'y':
        print("Export cancelled.")
        return
    
    # Export the model
    export_to_tflite(model_path)

if __name__ == "__main__":
    main()
