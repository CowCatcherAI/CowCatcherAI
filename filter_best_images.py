import os
import shutil
from ultralytics import YOLO

# ==========================================
# CONFIGURATION PARAMETERS
# ==========================================

# Path to your main folder containing subfolders (Input)
SOURCE_FOLDER = r"C:\cowcatcher\detections\mounts"

# Path where the top 3 should go (Output) in path as r"C:\cowcatcher\target_folder" or simply as folder name in same directory "target_folder"
TARGET_FOLDER = r"C:\cowcatcher\target_folder"

# Path to your trained YOLO model
MODEL_PATH = "cowcatcherV15.pt"

# Number of images to move per subfolder
NUM_TOP_IMAGES = 3

# NEW: Minimum confidence (0.0 to 1.0). 
# 0.5 means 50%. Anything below this is ignored.
MIN_CONFIDENCE_THRESHOLD = 0.1

# Valid extensions
VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}

# ==========================================
# MAIN SCRIPT
# ==========================================

def main():
    os.makedirs(TARGET_FOLDER, exist_ok=True)
    
    print(f"Loading model: {MODEL_PATH}...")
    try:
        model = YOLO(MODEL_PATH)
    except Exception as e:
        print(f"ERROR: Could not load model. Check the path. ({e})")
        return

    print(f"Starting scan of: {SOURCE_FOLDER}")
    print(f"Minimum score threshold: {MIN_CONFIDENCE_THRESHOLD}")

    for item in os.listdir(SOURCE_FOLDER):
        subfolder_path = os.path.join(SOURCE_FOLDER, item)
        
        if not os.path.isdir(subfolder_path):
            continue

        print(f"\n--- Processing subfolder: {item} ---")
        
        image_scores = []
        files = [f for f in os.listdir(subfolder_path) if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS]
        
        if not files:
            print("No images found.")
            continue

        # Run predictions
        for filename in files:
            full_path = os.path.join(subfolder_path, filename)
            
            # Run inference
            results = model(full_path, verbose=False)
            
            max_conf = 0.0
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    confs = boxes.conf.cpu().numpy()
                    if len(confs) > 0:
                        max_conf = max(confs)
            
            # Only add to list if score is high enough
            if max_conf >= MIN_CONFIDENCE_THRESHOLD:
                image_scores.append((filename, max_conf))
            else:
                # Optional: Print rejected files (commented out to keep output clean)
                # print(f"Ignored: {filename} (Score {max_conf:.2f} is too low)")
                pass

        # Sort from high to low
        image_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Take the top N (or fewer if fewer succeeded)
        best_selection = image_scores[:NUM_TOP_IMAGES]
        
        if len(best_selection) == 0:
            print(f"No image in '{item}' met the threshold of {MIN_CONFIDENCE_THRESHOLD}.")
        else:
            print(f"Selected top {len(best_selection)} (above threshold):")

            for filename, score in best_selection:
                source_file = os.path.join(subfolder_path, filename)
                new_name = f"{item}_{filename}"
                target_file = os.path.join(TARGET_FOLDER, new_name)
                
                print(f" -> Moving: {filename} (Score: {score:.2f})")
                shutil.move(source_file, target_file)

    print("\n--- Done! ---")

if __name__ == "__main__":
    main()
