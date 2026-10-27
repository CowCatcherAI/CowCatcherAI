import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
from ultralytics import YOLO

# Laad model
model = YOLO("yolo26m.pt")

# Train met augmentatie toegevoegd
model.train(
    data="dataset.yaml", 
    imgsz=640, 
    batch=16, 
    epochs=50,
    patience=10,
    #fraction=0.05, 
    save_period=5, 
    workers=0, 
    device=0,
    #close_mosaic=10,

    # Augmentatie instellingen
    augment=True,      
    degrees=10,        
    translate=0.1,     
    scale=0.5,         
    fliplr=0.5,        
    hsv_h=0.015,       
    hsv_s=0.7,         
    hsv_v=0.4,         
    mosaic=1.0         
)
