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
    epochs=400,
    patience=10,
    #fraction=0.05, #gebruikt in dit geval 100% van de dataset = 0,8 =80% van de set
    save_period=5, 
    workers=0, 
    device=0,

    # Augmentatie instellingen
    augment=True,      # Algemene augmentatie aan/uit
    degrees=10,        # Rotatie tot 10 graden
    translate=0.1,     # Translatie tot 10%
    scale=0.5,         # Schaling tussen 0.5 en 1.5
    fliplr=0.5,        # 50% kans op horizontaal spiegelen
    hsv_h=0.015,       # Kleine tint-variaties
    hsv_s=0.7,         # Verzadigingsvariaties
    hsv_v=0.4,         # Helderheidsvariaties
    mosaic=1.0         # Mosaic augmentatie (combinatie van 4 afbeeldingen)
)
