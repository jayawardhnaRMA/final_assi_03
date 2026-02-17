# YOLOv8 Chili Disease Detection

Train YOLOv8 model locally and deploy on Raspberry Pi 4 for real-time chili disease detection.

## Dataset

- **Classes**: 3 (antraknosa, cabai_normal, lalat_buah)
- **Images**: 1062 total
- **Format**: YOLOv8 (YOLO format with train/valid/test splits)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the Model Locally

```bash
python train.py
```

**Training Details:**
- Model: YOLOv8n (nano - optimized for Raspberry Pi)
- Image size: 416x416
- Epochs: 100
- Auto-detects GPU/CPU
- Training time: 1-3 hours (GPU) or 12-24 hours (CPU)

### 3. Export for Raspberry Pi

```bash
python export_for_pi.py
```

This converts the trained model to TensorFlow Lite INT8 format for optimal Raspberry Pi performance.

### 4. Deploy on Raspberry Pi

Transfer the exported model and inference script to your Raspberry Pi:

```bash
scp best_saved_model/best_int8.tflite pi@raspberrypi.local:~/
scp inference_pi.py pi@raspberrypi.local:~/
```

On Raspberry Pi, install dependencies:

```bash
pip install ultralytics opencv-python
```

Run inference on live camera feed:

```bash
python inference_pi.py --model best_int8.tflite
```

**Optional arguments:**
- `--no-display`: Run headless (no GUI)
- `--save-video`: Save output video
- `--frame-skip 2`: Process every 2nd frame for better FPS

## Performance Expectations

### Local Training
- **GPU (4GB+ VRAM)**: 1-3 hours
- **CPU**: 12-24 hours

### Raspberry Pi 4 Inference
- **FPS**: 10-15 (with INT8 optimization)
- **Resolution**: 416x416
- **Model size**: ~6-8 MB

## Project Structure

```
plant-disease-identification/
├── data/
│   ├── data.yaml           # Dataset configuration
│   ├── train/              # Training images and labels
│   ├── valid/              # Validation images and labels
│   └── test/               # Test images and labels
├── train.py                # Training script
├── export_for_pi.py        # Model export script
├── inference_pi.py         # Raspberry Pi inference script
├── requirements.txt        # Python dependencies
└── runs/                   # Training outputs (created after training)
    └── train/
        └── chili_disease_YYYYMMDD_HHMMSS/
            ├── weights/
            │   ├── best.pt
            │   └── last.pt
            └── results.png
```

## Optimization Tips

### For Better Accuracy
- Increase epochs: `epochs=150`
- Increase image size: `imgsz=640`
- Use larger model: `yolov8s.pt` (small) instead of nano

### For Better Raspberry Pi Performance
- Decrease image size: `imgsz=320`
- Skip frames: `--frame-skip 2`
- Use Coral USB Accelerator for 25-30 FPS

## Troubleshooting

**Out of memory during training:**
- Reduce batch size in `train.py`
- Use CPU instead of GPU
- Reduce image size to 320

**Slow inference on Pi:**
- Verify INT8 quantization was applied
- Reduce resolution to 320x320
- Use frame skipping
- Consider Coral USB Accelerator

**Low accuracy:**
- Train for more epochs
- Check data quality and annotations
- Try YOLOv8s (small) model
- Adjust confidence threshold

## Next Steps

1. Train the model: `python train.py`
2. Review results in `runs/train/chili_disease_*/`
3. Export for Pi: `python export_for_pi.py`
4. Test on Raspberry Pi

## Hardware Requirements

### Training
- **Minimum**: 8GB RAM, modern CPU
- **Recommended**: NVIDIA GPU with 4GB+ VRAM

### Deployment
- Raspberry Pi 4 (4GB recommended)
- Camera (USB or Pi Camera Module)
- Optional: Google Coral USB Accelerator for better FPS

## License

Dataset: Public Domain
