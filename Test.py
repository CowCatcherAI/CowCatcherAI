from ultralytics import YOLO
import os
import numpy as np
import pandas as pd
from pathlib import Path
import glob
import datetime
import cv2

# ====== CONFIGURABLE PARAMETERS ======
models = [
    #"cowcatcherv10",
    #"cowcatcherV12.pt",
    "cowcatcherV13.pt",
]  # List of model paths

# Directory paths (easy to modify)
source_dir = r"C:/cowcatcher/test/images"  # Source directory with images
labels_dir = r"C:/cowcatcher/test/labels"  # Directory with ground truth labels
base_destination_dir = r"C:/cowcatcher/test"  # Base destination directory for results

confidence_threshold = 0.7  # Minimum confidence for YOLO filtering
detection_threshold = 0.85  # Minimum confidence for "Detected" status
conf_bins = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.83, 0.86, 0.88, 0.9, 1.0]  # Bins for confidence scores

# Excel filename for summarizing results
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
excel_output = os.path.join(base_destination_dir, f"detailed_model_comparison_{timestamp}.xlsx")

def collect_images_with_labels(source_dir, labels_dir):
    """
    Collect only images that also have a corresponding label file
    """
    print("🔍 Searching for images with corresponding labels...")
    
    # Find all label files
    label_files = glob.glob(os.path.join(labels_dir, "*.txt"))
    label_names = {Path(label_file).stem for label_file in label_files}
    
    print(f"✓ Found {len(label_names)} label files in {labels_dir}")
    
    # Search for images that match the label names
    image_files = []
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    
    for label_name in label_names:
        # Search for image with this name in different extensions
        found_image = False
        for ext in image_extensions:
            potential_image = os.path.join(source_dir, f"{label_name}{ext}")
            if os.path.exists(potential_image):
                image_files.append(potential_image)
                found_image = True
                break  # Stop searching once we found a match
        
        if not found_image:
            print(f"⚠️  No image found for label: {label_name}")
    
    print(f"✓ Found {len(image_files)} images with corresponding labels")
    
    # Check for duplicate files (for safety)
    unique_stems = {Path(img).stem for img in image_files}
    if len(unique_stems) != len(image_files):
        print(f"⚠️  Warning: {len(image_files) - len(unique_stems)} duplicate images detected!")
        # Remove duplicates
        seen_stems = set()
        unique_image_files = []
        for img in image_files:
            stem = Path(img).stem
            if stem not in seen_stems:
                unique_image_files.append(img)
                seen_stems.add(stem)
        image_files = unique_image_files
        print(f"✓ After deduplication: {len(image_files)} unique images")
    
    return image_files

def load_ground_truth_labels(labels_dir, image_files):
    """
    Load ground truth labels for all images
    Returns: dict with {image_name: has_mounting_label}
    """
    ground_truth = {}
    total_images = len(image_files)
    
    print(f"Loading ground truth labels for {total_images} images...")
    print("Progress: ", end="", flush=True)
    
    for i, img_path in enumerate(image_files, 1):
        img_name = Path(img_path).stem  # Filename without extension
        label_path = os.path.join(labels_dir, f"{img_name}.txt")
        
        has_mounting = False
        if os.path.exists(label_path):
            try:
                with open(label_path, 'r') as f:
                    lines = f.readlines()
                    # Check if there's a line starting with "0" (mounting class)
                    for line in lines:
                        if line.strip().startswith('0 '):
                            has_mounting = True
                            break
            except Exception as e:
                print(f"Error reading label {label_path}: {e}")
        
        ground_truth[img_name] = has_mounting
        
        # Show progress every 50 images or at the last image
        if i % 50 == 0 or i == total_images:
            progress_percent = (i / total_images) * 100
            print(f"\rProgress: {i}/{total_images} ({progress_percent:.1f}%) ", end="", flush=True)
    
    print()  # New line after completion
    return ground_truth

def run_detection_on_images(model_path, image_files):
    """
    Run detections with the given model on all images
    Returns: dict with {image_name: max_confidence}
    """
    model = YOLO(model_path)
    model_name = os.path.basename(model_path).replace('.pt', '')
    
    print(f"Processing {len(image_files)} images with model {model_name}")
    print("Progress: ", end="", flush=True)
    
    results_dict = {}
    total_images = len(image_files)
    
    failed_images = []
    
    for i, img_path in enumerate(image_files, 1):
        img_name = Path(img_path).stem
        max_confidence = 0.0  # Default: no detection
        
        try:
            # Check if file exists and is accessible
            if not os.path.exists(img_path):
                print(f"\n⚠️  File not found: {img_path}")
                failed_images.append(img_name)
                continue
                
            # Run detection with only mounting class (class 0)
            results = model.predict(source=img_path, classes=[0], conf=confidence_threshold, 
                                   save=False, verbose=False)
            
            # Find the highest confidence score for this image
            for result in results:
                if result.boxes and len(result.boxes) > 0:
                    conf_values = result.boxes.conf.cpu().numpy()
                    max_confidence = float(np.max(conf_values))
                    
        except KeyboardInterrupt:
            print(f"\n❌ Script stopped by user at image {i}/{total_images}")
            print(f"Processed images so far: {i-1}")
            raise
        except Exception as e:
            print(f"\n⚠️  Error processing {img_name}: {str(e)}")
            failed_images.append(img_name)
            max_confidence = 0.0
        
        results_dict[img_name] = max_confidence
        
        # Show progress every 10 images or at the last image
        if i % 10 == 0 or i == total_images:
            progress_percent = (i / total_images) * 100
            print(f"\rProgress: {i}/{total_images} ({progress_percent:.1f}%) ", end="", flush=True)
    
    print()  # New line after completion
    
    if failed_images:
        print(f"⚠️  {len(failed_images)} images could not be processed: {failed_images[:5]}{'...' if len(failed_images) > 5 else ''}")
    
    return results_dict

def create_detailed_comparison_table(image_files, model_results, ground_truth, models):
    """
    Create a detailed comparison table per image
    """
    model_names = [os.path.basename(m).replace('.pt', '') for m in models]
    
    # Create a list with all data
    data = []
    
    for img_path in image_files:
        img_name = Path(img_path).stem
        
        row = {
            'Image_Name': img_name,
            'Ground_Truth_Has_Mounting': ground_truth.get(img_name, False)
        }
        
        # Add confidence values for each model
        for model_name in model_names:
            confidence = model_results[model_name].get(img_name, 0.0)
            row[f'{model_name}_Confidence'] = confidence
            row[f'{model_name}_Detected'] = confidence >= detection_threshold
        
        data.append(row)
    
    return pd.DataFrame(data)

def calculate_model_performance(detailed_df, model_names):
    """
    Calculate performance metrics for each model
    """
    performance_data = []
    
    for model_name in model_names:
        detected_col = f'{model_name}_Detected'
        confidence_col = f'{model_name}_Confidence'
        
        # True Positives: Ground truth = True AND Model detected = True  
        tp = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == True) & 
                            (detailed_df[detected_col] == True)])
        
        # False Positives: Ground truth = False AND Model detected = True
        fp = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == False) & 
                            (detailed_df[detected_col] == True)])
        
        # False Negatives: Ground truth = True AND Model detected = False
        fn = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == True) & 
                            (detailed_df[detected_col] == False)])
        
        # True Negatives: Ground truth = False AND Model detected = False
        tn = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == False) & 
                            (detailed_df[detected_col] == False)])
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        
        # Average confidence of detections (above detection threshold)
        detected_confidences = detailed_df[detailed_df[detected_col] == True][confidence_col]
        avg_confidence = detected_confidences.mean() if len(detected_confidences) > 0 else 0
        
        # Also statistics for all detections above YOLO threshold
        all_detected_confidences = detailed_df[detailed_df[confidence_col] >= confidence_threshold][confidence_col]
        total_yolo_detections = len(all_detected_confidences)
        
        performance_data.append({
            'Model': model_name,
            'True_Positives': tp,
            'False_Positives': fp,
            'False_Negatives': fn,
            'True_Negatives': tn,
            'Precision': round(precision, 4),
            'Recall': round(recall, 4),
            'F1_Score': round(f1_score, 4),
            'Accuracy': round(accuracy, 4),
            'Detections_Above_Detection_Threshold': tp + fp,
            'Total_YOLO_Detections_Above_Confidence_Threshold': total_yolo_detections,
            'Avg_Confidence_When_Detected': round(avg_confidence, 4),
            'Detection_Threshold_Used': detection_threshold,
            'YOLO_Confidence_Threshold_Used': confidence_threshold
        })
    
    return pd.DataFrame(performance_data)

def create_confidence_distribution_analysis(detailed_df, model_names):
    """
    Analyze the distribution of confidence scores - transposed version
    """
    # Create a dictionary to collect all data
    all_data = {}
    
    for model_name in model_names:
        confidence_col = f'{model_name}_Confidence'
        
        # All confidence values (including 0 for no detection)
        all_confidences = detailed_df[confidence_col].values
        detected_confidences = detailed_df[detailed_df[confidence_col] >= detection_threshold][confidence_col].values
        yolo_detections = detailed_df[detailed_df[confidence_col] >= confidence_threshold][confidence_col].values
        
        # Calculate distribution over bins (use YOLO detections for histogram)
        counts, _ = np.histogram(yolo_detections, bins=conf_bins)
        
        model_data = {}
        
        # Add bins
        for i in range(len(conf_bins)-1):
            bin_range = f"{conf_bins[i]:.1f}-{conf_bins[i+1]:.1f}"
            model_data[bin_range] = counts[i]
        
        # Add statistics
        model_data['Total_Images'] = len(all_confidences)
        model_data['Images_Above_Detection_Threshold'] = len(detected_confidences)
        model_data['Images_Above_YOLO_Threshold'] = len(yolo_detections)
        model_data['Images_Without_Detection'] = len(all_confidences) - len(yolo_detections)
        model_data['Detection_Rate_Above_Detection_Threshold'] = round(len(detected_confidences) / len(all_confidences), 4)
        model_data['Detection_Rate_Above_YOLO_Threshold'] = round(len(yolo_detections) / len(all_confidences), 4)
        
        # Statistics based on detections above detection threshold
        if len(detected_confidences) > 0:
            model_data['Min_Confidence_Detected'] = round(np.min(detected_confidences), 4)
            model_data['Max_Confidence_Detected'] = round(np.max(detected_confidences), 4)
            model_data['Mean_Confidence_Detected'] = round(np.mean(detected_confidences), 4)
            model_data['Median_Confidence_Detected'] = round(np.median(detected_confidences), 4)
        else:
            model_data['Min_Confidence_Detected'] = 0
            model_data['Max_Confidence_Detected'] = 0
            model_data['Mean_Confidence_Detected'] = 0
            model_data['Median_Confidence_Detected'] = 0
            
        # Statistics based on all YOLO detections
        if len(yolo_detections) > 0:
            model_data['Min_Confidence_YOLO'] = round(np.min(yolo_detections), 4)
            model_data['Max_Confidence_YOLO'] = round(np.max(yolo_detections), 4)
            model_data['Mean_Confidence_YOLO'] = round(np.mean(yolo_detections), 4)
            model_data['Median_Confidence_YOLO'] = round(np.median(yolo_detections), 4)
        else:
            model_data['Min_Confidence_YOLO'] = 0
            model_data['Max_Confidence_YOLO'] = 0
            model_data['Mean_Confidence_YOLO'] = 0
            model_data['Median_Confidence_YOLO'] = 0
        
        # Save all data for this model
        all_data[model_name] = model_data
    
    # Convert to DataFrame and transpose
    df = pd.DataFrame(all_data)
    
    # Ensure correct order of rows (metrics)
    desired_order = []
    
    # First the confidence bins in order
    for i in range(len(conf_bins)-1):
        bin_range = f"{conf_bins[i]:.1f}-{conf_bins[i+1]:.1f}"
        desired_order.append(bin_range)
    
    # Then the other statistics
    other_metrics = [
        'Total_Images',
        'Images_Above_Detection_Threshold', 
        'Images_Above_YOLO_Threshold',
        'Images_Without_Detection',
        'Detection_Rate_Above_Detection_Threshold',
        'Detection_Rate_Above_YOLO_Threshold',
        'Min_Confidence_Detected',
        'Max_Confidence_Detected', 
        'Mean_Confidence_Detected',
        'Median_Confidence_Detected',
        'Min_Confidence_YOLO',
        'Max_Confidence_YOLO',
        'Mean_Confidence_YOLO',
        'Median_Confidence_YOLO'
    ]
    desired_order.extend(other_metrics)
    
    # Reorder the rows
    df = df.reindex(desired_order)
    
    # Reset index so metric names become a column
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Metric'}, inplace=True)
    
    return df

def find_problematic_images(detailed_df, model_names):
    """
    Find images where models disagree or are wrong
    """
    problematic = []
    
    for _, row in detailed_df.iterrows():
        img_name = row['Image_Name']
        ground_truth = row['Ground_Truth_Has_Mounting']
        
        # Collect all model predictions
        model_predictions = []
        model_confidences = []
        
        for model_name in model_names:
            detected = row[f'{model_name}_Detected']
            confidence = row[f'{model_name}_Confidence']
            model_predictions.append(detected)
            model_confidences.append(confidence)
        
        # Check for problems
        issues = []
        
        # Models disagree
        if not all(pred == model_predictions[0] for pred in model_predictions):
            issues.append("Models_Disagree")
        
        # All models wrong (if there is ground truth)
        if all(pred != ground_truth for pred in model_predictions):
            issues.append("All_Models_Wrong")
        
        # Some models wrong
        elif any(pred != ground_truth for pred in model_predictions):
            issues.append("Some_Models_Wrong")
        
        if issues:
            problem_row = {
                'Image_Name': img_name,
                'Ground_Truth': ground_truth,
                'Issues': ', '.join(issues)
            }
            
            # Add model results
            for i, model_name in enumerate(model_names):
                problem_row[f'{model_name}_Detected'] = model_predictions[i]
                problem_row[f'{model_name}_Confidence'] = model_confidences[i]
            
            problematic.append(problem_row)
    
    return pd.DataFrame(problematic)

def main():
    print("🚀 Starting improved model comparison...")
    
    # Check if all model files exist
    missing_models = []
    for model_path in models:
        if not os.path.exists(model_path):
            missing_models.append(model_path)
    
    if missing_models:
        print("❌ The following model files were not found:")
        for model in missing_models:
            print(f"   - {model}")
        print("Check the paths in the configuration section.")
        return
    
    # Create output directory
    try:
        os.makedirs(os.path.dirname(excel_output), exist_ok=True)
    except Exception as e:
        print(f"❌ Could not create output directory: {e}")
        return
    
    # Collect only images that also have labels
    image_files = collect_images_with_labels(source_dir, labels_dir)
    
    if not image_files:
        print(f"❌ No images with corresponding labels found")
        print(f"   Source dir: {source_dir}")
        print(f"   Labels dir: {labels_dir}")
        return
    
    print(f"✓ Working with {len(image_files)} images that have labels")
    
    # Check if the labels directory exists
    if not os.path.exists(labels_dir):
        print(f"⚠️  Labels directory not found: {labels_dir}")
        print("Script will continue without ground truth labels.")
        use_ground_truth = False
    else:
        use_ground_truth = True
    
    # Load ground truth labels
    print("=" * 60)
    if use_ground_truth:
        ground_truth = load_ground_truth_labels(labels_dir, image_files)
        mounting_images = sum(1 for has_mounting in ground_truth.values() if has_mounting)
        print(f"✓ Ground truth loaded: {mounting_images} images with mounting labels")
    else:
        # Create dummy ground truth if labels are not available
        ground_truth = {Path(img).stem: False for img in image_files}
        mounting_images = 0
        print("⚠️  No ground truth available - performance metrics will not be accurate")
    
    # Run detections for each model
    model_results = {}
    model_names = []
    
    for model_idx, model_path in enumerate(models, 1):
        model_name = os.path.basename(model_path).replace('.pt', '')
        model_names.append(model_name)
        print(f"\n{'='*60}")
        print(f"MODEL {model_idx}/{len(models)}: {model_name}")
        print(f"{'='*60}")
        
        model_results[model_name] = run_detection_on_images(model_path, image_files)
        
        total_detections = sum(1 for conf in model_results[model_name].values() if conf > 0)
        high_conf_detections = sum(1 for conf in model_results[model_name].values() if conf >= detection_threshold)
        print(f"✓ Model {model_name} completed:")
        print(f"  - {total_detections} detections above YOLO threshold ({confidence_threshold})")
        print(f"  - {high_conf_detections} detections above detection threshold ({detection_threshold})")
    
    # Create detailed comparison table
    print(f"\n{'='*60}")
    print("ANALYZING RESULTS")
    print(f"{'='*60}")
    print("📊 Creating detailed comparison table...")
    detailed_df = create_detailed_comparison_table(image_files, model_results, ground_truth, models)
    
    # Calculate performance metrics
    print("📈 Calculating performance metrics...")
    performance_df = calculate_model_performance(detailed_df, model_names)
    
    # Create confidence distribution analysis
    print("📉 Analyzing confidence distributions...")
    distribution_df = create_confidence_distribution_analysis(detailed_df, model_names)
    
    # Find problematic images
    print("🔍 Searching for problematic images...")
    problematic_df = find_problematic_images(detailed_df, model_names)
    
    # Save everything to Excel
    print(f"\n{'='*60}")
    print("SAVING RESULTS")
    print(f"{'='*60}")
    print(f"💾 Saving results to Excel...")
    print(f"📁 File: {excel_output}")
    
    with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
        # Performance summary (best model on top)
        performance_sorted = performance_df.sort_values('F1_Score', ascending=False)
        performance_sorted.to_excel(writer, sheet_name='Model Performance', index=False)
        
        # Detailed results per image
        detailed_df.to_excel(writer, sheet_name='Detailed Results', index=False)
        
        # Confidence distribution (now transposed)
        distribution_df.to_excel(writer, sheet_name='Confidence Distribution', index=False)
        
        # Problematic images
        if not problematic_df.empty:
            problematic_df.to_excel(writer, sheet_name='Problematic Images', index=False)
        
        # Ground truth summary
        gt_summary = pd.DataFrame({
            'Metric': ['Total Images', 'Images with Mounting', 'Images without Mounting'],
            'Count': [
                len(ground_truth),
                sum(1 for has_mounting in ground_truth.values() if has_mounting),
                sum(1 for has_mounting in ground_truth.values() if not has_mounting)
            ]
        })
        gt_summary.to_excel(writer, sheet_name='Ground Truth Summary', index=False)
    
    print("✓ Excel file successfully saved!")
    
    # Print summary
    print(f"\n{'='*70}")
    print("🎯 FINAL RESULTS SUMMARY")
    print(f"{'='*70}")
    
    print(f"Total number of images: {len(image_files)}")
    print(f"Images with mounting labels: {mounting_images}")
    print(f"Images without mounting labels: {len(ground_truth) - mounting_images}")
    print(f"YOLO confidence threshold: {confidence_threshold}")
    print(f"Detection threshold: {detection_threshold}")
    
    print(f"\nMODEL PERFORMANCE (sorted by F1-Score):")
    print("-" * 80)
    for _, row in performance_sorted.iterrows():
        print(f"{row['Model']:15} | F1: {row['F1_Score']:.3f} | "
              f"Precision: {row['Precision']:.3f} | Recall: {row['Recall']:.3f} | "
              f"Accuracy: {row['Accuracy']:.3f} | "
              f"Detected: {row['Detections_Above_Detection_Threshold']} | "
              f"YOLO: {row['Total_YOLO_Detections_Above_Confidence_Threshold']}")
    
    best_model = performance_sorted.iloc[0]['Model']
    best_f1 = performance_sorted.iloc[0]['F1_Score']
    print(f"\n🏆 BEST MODEL: {best_model} (F1-Score: {best_f1:.3f})")
    
    if not problematic_df.empty:
        print(f"\n⚠️  Number of problematic images: {len(problematic_df)}")
    
    print(f"\nAll detailed results are saved in:")
    print(f"{excel_output}")

if __name__ == "__main__":
    main()
