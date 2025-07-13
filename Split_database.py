import os
import sys
import shutil
import random

# Configuration parameters
TRAIN_RATIO = 0.6
VALID_RATIO = 0.3
TEST_RATIO = 0.1
CREATE_YAML = True

# Default folder paths - modify these to match your setup
DEFAULT_IMAGES_FOLDER = "DISK:/Path/annotated_images"
DEFAULT_LABELS_FOLDER = "Disk:/Path/annotated_labels"
DEFAULT_TRAIN_FOLDER = "Disk:/Path/train"
DEFAULT_VALID_FOLDER = "Disk:/Path/valid"
DEFAULT_TEST_FOLDER = "Disk:/Path/test"

def split_yolo_dataset(images_folder, labels_folder, train_folder, valid_folder, test_folder=None, 
                      train_ratio=TRAIN_RATIO, valid_ratio=VALID_RATIO, test_ratio=TEST_RATIO, create_yaml=CREATE_YAML):
    """
    Split YOLO dataset into train/valid/test sets.
    
    Args:
        images_folder (str): Path to folder with images
        labels_folder (str): Path to folder with labels
        train_folder (str): Path to train output folder
        valid_folder (str): Path to valid output folder
        test_folder (str): Path to test output folder (optional)
        train_ratio (float): Training set ratio (default 0.7)
        valid_ratio (float): Validation set ratio (default 0.2)
        test_ratio (float): Test set ratio (default 0.1, set to 0 to skip)
        create_yaml (bool): Create YAML config file (default False)
    """
    
    # If no test folder provided or test_ratio is 0, disable test set
    if test_folder is None or test_ratio == 0:
        test_ratio = 0
        # Normalize train/valid ratios
        total = train_ratio + valid_ratio
        train_ratio = train_ratio / total
        valid_ratio = valid_ratio / total
        print(f"Test set disabled. Adjusted ratios - Train: {train_ratio:.1f}, Valid: {valid_ratio:.1f}")
    else:
        # Check if ratios sum to 1
        total_ratio = train_ratio + valid_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.01:
            print(f"Warning: Ratios sum to {total_ratio}, not 1.0. Normalizing...")
            train_ratio /= total_ratio
            valid_ratio /= total_ratio
            test_ratio /= total_ratio
    
    # Check source folders
    if not os.path.exists(images_folder):
        print(f"Error: Images folder not found: {images_folder}")
        return False
        
    if not os.path.exists(labels_folder):
        print(f"Error: Labels folder not found: {labels_folder}")
        return False
    
    # Create directory structure
    folders_to_create = [
        os.path.join(train_folder, "images"),
        os.path.join(train_folder, "labels"),
        os.path.join(valid_folder, "images"),
        os.path.join(valid_folder, "labels")
    ]
    
    if test_ratio > 0 and test_folder:
        folders_to_create.extend([
            os.path.join(test_folder, "images"),
            os.path.join(test_folder, "labels")
        ])
    
    for folder in folders_to_create:
        os.makedirs(folder, exist_ok=True)
    
    # Find image files with corresponding labels
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    valid_pairs = []
    
    for filename in os.listdir(images_folder):
        name, ext = os.path.splitext(filename)
        if ext.lower() in image_extensions:
            image_path = os.path.join(images_folder, filename)
            label_path = os.path.join(labels_folder, name + '.txt')
            
            if os.path.exists(label_path):
                valid_pairs.append({
                    'image_file': filename,
                    'label_file': name + '.txt',
                    'image_path': image_path,
                    'label_path': label_path
                })
            else:
                print(f"Warning: No label found for {filename}")
    
    if not valid_pairs:
        print("Error: No valid image-label pairs found!")
        return False
    
    # Shuffle data
    random.shuffle(valid_pairs)
    
    # Calculate splits
    total_files = len(valid_pairs)
    train_count = int(total_files * train_ratio)
    valid_count = int(total_files * valid_ratio)
    test_count = total_files - train_count - valid_count if test_ratio > 0 else 0
    
    # Split data
    train_data = valid_pairs[:train_count]
    valid_data = valid_pairs[train_count:train_count + valid_count]
    test_data = valid_pairs[train_count + valid_count:] if test_ratio > 0 else []
    
    # Copy files function
    def copy_files(data_list, dest_folder, set_name):
        images_dest = os.path.join(dest_folder, "images")
        labels_dest = os.path.join(dest_folder, "labels")
        
        for item in data_list:
            # Copy image
            shutil.copy2(item['image_path'], os.path.join(images_dest, item['image_file']))
            # Copy label
            shutil.copy2(item['label_path'], os.path.join(labels_dest, item['label_file']))
    
    # Copy files to respective folders
    copy_files(train_data, train_folder, "training")
    copy_files(valid_data, valid_folder, "validation")
    
    if test_ratio > 0 and test_data and test_folder:
        copy_files(test_data, test_folder, "test")
    
    # Create YAML configuration
    if create_yaml:
        # Use parent directory of train folder for yaml location
        yaml_path = os.path.join(os.path.dirname(train_folder), 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            f.write(f'train: {train_folder}/images\n')
            f.write(f'val: {valid_folder}/images\n')
            if test_ratio > 0 and test_folder:
                f.write(f'test: {test_folder}/images\n')
            f.write('nc: 1\n')
            f.write("names: ['mounting']\n")
        print(f"YAML configuration created: {yaml_path}")
    
    # Print summary
    print(f"\nDataset successfully split:")
    print(f"Total number of images: {total_files}")
    print(f"Training set: {len(train_data)} images ({len(train_data)/total_files*100:.1f}%)")
    print(f"Validation set: {len(valid_data)} images ({len(valid_data)/total_files*100:.1f}%)")
    
    if test_ratio > 0:
        print(f"Test set: {len(test_data)} images ({len(test_data)/total_files*100:.1f}%)")
    else:
        print(f"Test set: Skipped (test_ratio=0)")
    
    print(f"\nFolder locations:")
    print(f"Train images: {os.path.join(train_folder, 'images')}")
    print(f"Train labels: {os.path.join(train_folder, 'labels')}")
    print(f"Valid images: {os.path.join(valid_folder, 'images')}")
    print(f"Valid labels: {os.path.join(valid_folder, 'labels')}")
    
    if test_ratio > 0 and test_folder:
        print(f"Test images: {os.path.join(test_folder, 'images')}")
        print(f"Test labels: {os.path.join(test_folder, 'labels')}")
    
    if create_yaml:
        print(f"\nYAML configuration file created: {yaml_path}")
    else:
        print(f"\nNo YAML configuration file created (create_yaml=False)")
    
    return True

def main():
    if len(sys.argv) < 2:
        print("Dataset Splitter")
        print("=" * 50)
        print("Usage:")
        print("  python split_dataset.py [images_folder] [labels_folder] [train_folder] [valid_folder] [test_folder] [train_ratio] [valid_ratio] [test_ratio] [create_yaml]")
        print()
        print("Current default settings:")
        print(f"  Images folder: {DEFAULT_IMAGES_FOLDER}")
        print(f"  Labels folder: {DEFAULT_LABELS_FOLDER}")
        print(f"  Train folder:  {DEFAULT_TRAIN_FOLDER}")
        print(f"  Valid folder:  {DEFAULT_VALID_FOLDER}")
        print(f"  Test folder:   {DEFAULT_TEST_FOLDER}")
        print(f"  Ratios: {TRAIN_RATIO}/{VALID_RATIO}/{TEST_RATIO}")
        print()
        print("  # With test set using default ratios")
        print(f"  python split_dataset.py {DEFAULT_IMAGES_FOLDER} {DEFAULT_LABELS_FOLDER} {DEFAULT_TRAIN_FOLDER} {DEFAULT_VALID_FOLDER} {DEFAULT_TEST_FOLDER}")
        print()
        print("  # Custom ratios with test set and YAML configuration")
        print(f"  python split_dataset.py {DEFAULT_IMAGES_FOLDER} {DEFAULT_LABELS_FOLDER} {DEFAULT_TRAIN_FOLDER} {DEFAULT_VALID_FOLDER} {DEFAULT_TEST_FOLDER} 0.6 0.2 0.2 1")
        print()
        print("  # Usage without test folder")
        print(f"  python split_dataset.py {DEFAULT_IMAGES_FOLDER} {DEFAULT_LABELS_FOLDER} {DEFAULT_TRAIN_FOLDER} {DEFAULT_VALID_FOLDER}")
        return

    # Parse arguments with defaults
    images_folder = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "" else DEFAULT_IMAGES_FOLDER
    labels_folder = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "" else DEFAULT_LABELS_FOLDER
    train_folder = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "" else DEFAULT_TRAIN_FOLDER
    valid_folder = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "" else DEFAULT_VALID_FOLDER
    
    # Check if test folder is provided or use default
    if len(sys.argv) >= 6:
        test_folder = sys.argv[5] if sys.argv[5] != "" else DEFAULT_TEST_FOLDER
        # Optional parameters with defaults
        train_ratio = float(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != "" else TRAIN_RATIO
        valid_ratio = float(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7] != "" else VALID_RATIO
        test_ratio = float(sys.argv[8]) if len(sys.argv) > 8 and sys.argv[8] != "" else TEST_RATIO
        create_yaml = bool(int(sys.argv[9])) if len(sys.argv) > 9 and sys.argv[9] != "" else CREATE_YAML
    elif len(sys.argv) == 5:
        # Original 4-argument usage (train/valid only)
        test_folder = None
        train_ratio = TRAIN_RATIO
        valid_ratio = 1.0 - TRAIN_RATIO  # Use remaining for validation
        test_ratio = 0
        create_yaml = CREATE_YAML
    else:
        # Use all defaults including test folder
        test_folder = DEFAULT_TEST_FOLDER
        train_ratio = TRAIN_RATIO
        valid_ratio = VALID_RATIO
        test_ratio = TEST_RATIO
        create_yaml = CREATE_YAML
    
    print(f"Starting dataset split...")
    print(f"Images: {images_folder}")
    print(f"Labels: {labels_folder}")
    print(f"Train folder: {train_folder}")
    print(f"Valid folder: {valid_folder}")
    if test_folder:
        print(f"Test folder: {test_folder}")
    print(f"Ratios: Train={train_ratio}, Valid={valid_ratio}, Test={test_ratio}")
    print(f"Create YAML: {create_yaml}")
    print("-" * 50)
    
    success = split_yolo_dataset(
        images_folder=images_folder,
        labels_folder=labels_folder,
        train_folder=train_folder,
        valid_folder=valid_folder,
        test_folder=test_folder,
        train_ratio=train_ratio,
        valid_ratio=valid_ratio,
        test_ratio=test_ratio,
        create_yaml=create_yaml
    )
    
    if success:
        print(f"\n✅ Dataset split completed successfully!")
    else:
        print(f"\n❌ Dataset split failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
