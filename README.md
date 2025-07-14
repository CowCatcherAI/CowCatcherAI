# CowCatcherAI - GitHub Repository Structure

```
CowCatcherAI/
├── LICENSE
├── README.md
├── dataset.yaml                    # Dataset configuration for training
├── config.py                       # Configuration settings
├── run_python_script.bat          # Quick startup script
├── models/
│   ├── CowcatcherVx.pt            # Main AI model file
│   └── yolo11m.pt                 # Optional YOLO base model
├── src/
│   ├── cowcatcher.py              # Main detection program
│   ├── train.py                   # Training script for YOLO/fine-tuning
│   ├── annotate_helper.py         # Image annotation utility
│   └── split_database.py          # Dataset splitting utility
├── data/
│   ├── mounting_detections/       # Raw detection results
│   ├── annotate/                  # Images to be annotated
│   ├── delete/                    # Images annotated
│   ├── annotated_images/          # Manually annotated images
│   ├── annotated_labels/          # Corresponding label files
│   ├── train/                     # Training dataset
│   │   ├── images/
│   │   └── labels/
│   ├── val/                       # Validation dataset
│   │   ├── images/
│   │   └── labels/
│   └── test/                      # Optional test dataset
│       ├── images/
│       └── labels/
```

