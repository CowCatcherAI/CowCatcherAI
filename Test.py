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
excel_output = os.path.join(base_destination_dir, f"model_comparison_summary_{timestamp}.xlsx")

def collect_images_with_labels(source_dir, labels_dir):
    """
    Collect only images that also have a corresponding label file
    """
    print("🔍 Searching for images with corresponding labels...")
    
    label_files = glob.glob(os.path.join(labels_dir, "*.txt"))
    label_names = {Path(label_file).stem for label_file in label_files}
    
    print(f"✓ Found {len(label_names)} label files in {labels_dir}")
    
    image_files = []
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    
    for label_name in label_names:
        found_image = False
        for ext in image_extensions:
            potential_image = os.path.join(source_dir, f"{label_name}{ext}")
            if os.path.exists(potential_image):
                image_files.append(potential_image)
                found_image = True
                break 
        
        if not found_image:
            print(f"⚠️  No image found for label: {label_name}")
    
    print(f"✓ Found {len(image_files)} images with corresponding labels")
    
    unique_stems = {Path(img).stem for img in image_files}
    if len(unique_stems) != len(image_files):
        print(f"⚠️  Warning: {len(image_files) - len(unique_stems)} duplicate images detected!")
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
    """
    ground_truth = {}
    total_images = len(image_files)
    
    print(f"Loading ground truth labels for {total_images} images...")
    print("Progress: ", end="", flush=True)
    
    for i, img_path in enumerate(image_files, 1):
        img_name = Path(img_path).stem 
        label_path = os.path.join(labels_dir, f"{img_name}.txt")
        
        has_mounting = False
        if os.path.exists(label_path):
            try:
                with open(label_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip().startswith('0 '):
                            has_mounting = True
                            break
            except Exception as e:
                print(f"Error reading label {label_path}: {e}")
        
        ground_truth[img_name] = has_mounting
        
        if i % 50 == 0 or i == total_images:
            progress_percent = (i / total_images) * 100
            print(f"\rProgress: {i}/{total_images} ({progress_percent:.1f}%) ", end="", flush=True)
    
    print()
    return ground_truth

def run_detection_on_images(model_path, image_files):
    """
    Run detections with the given model on all images
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
        max_confidence = 0.0 
        
        try:
            if not os.path.exists(img_path):
                print(f"\n⚠️  File not found: {img_path}")
                failed_images.append(img_name)
                continue
                
            results = model.predict(source=img_path, classes=[0], conf=confidence_threshold, 
                                   save=False, verbose=False)
            
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
        
        if i % 10 == 0 or i == total_images:
            progress_percent = (i / total_images) * 100
            print(f"\rProgress: {i}/{total_images} ({progress_percent:.1f}%) ", end="", flush=True)
    
    print()
    if failed_images:
        print(f"⚠️  {len(failed_images)} images could not be processed: {failed_images[:5]}{'...' if len(failed_images) > 5 else ''}")
    
    return results_dict

def create_detailed_comparison_table(image_files, model_results, ground_truth, models):
    """
    Create a detailed comparison table per image in the background (used for metric calculations)
    """
    model_names = [os.path.basename(m).replace('.pt', '') for m in models]
    data = []
    
    for img_path in image_files:
        img_name = Path(img_path).stem
        row = {
            'Image_Name': img_name,
            'Ground_Truth_Has_Mounting': ground_truth.get(img_name, False)
        }
        
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
        
        tp = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == True) & 
                            (detailed_df[detected_col] == True)])
        fp = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == False) & 
                            (detailed_df[detected_col] == True)])
        fn = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == True) & 
                            (detailed_df[detected_col] == False)])
        tn = len(detailed_df[(detailed_df['Ground_Truth_Has_Mounting'] == False) & 
                            (detailed_df[detected_col] == False)])
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        
        # Gemiddelde confidence ALLEEN voor True Positives
        tp_confidences = detailed_df[(detailed_df[detected_col] == True) & 
                                     (detailed_df['Ground_Truth_Has_Mounting'] == True)][confidence_col]
        avg_tp_confidence = tp_confidences.mean() if len(tp_confidences) > 0 else 0
        
        # Aantal YOLO detecties dat daadwerkelijk een True Positive is
        tp_yolo_confidences = detailed_df[(detailed_df[confidence_col] >= confidence_threshold) & 
                                          (detailed_df['Ground_Truth_Has_Mounting'] == True)][confidence_col]
        total_tp_yolo_detections = len(tp_yolo_confidences)
        
        # NIEUW: Gemiddelde confidence ALLEEN voor False Negatives
        fn_confidences = detailed_df[(detailed_df[detected_col] == False) & 
                                     (detailed_df['Ground_Truth_Has_Mounting'] == True)][confidence_col]
        avg_fn_confidence = fn_confidences.mean() if len(fn_confidences) > 0 else 0
        
        # NIEUW: Aantal YOLO detecties dat een False Negative is (dus score >= yolo threshold, maar < detection threshold)
        fn_yolo_confidences = detailed_df[(detailed_df[confidence_col] >= confidence_threshold) & 
                                          (detailed_df[detected_col] == False) &
                                          (detailed_df['Ground_Truth_Has_Mounting'] == True)][confidence_col]
        total_fn_yolo_detections = len(fn_yolo_confidences)
        
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
            'Total_Detections': tp + fp,
            'True_Positive_YOLO_Detections': total_tp_yolo_detections,
            'Avg_Confidence_True_Positives': round(avg_tp_confidence, 4),
            'False_Negative_YOLO_Detections': total_fn_yolo_detections,
            'Avg_Confidence_False_Negatives': round(avg_fn_confidence, 4),
            'Detection_Threshold_Used': detection_threshold,
            'YOLO_Confidence_Threshold_Used': confidence_threshold
        })
    
    return pd.DataFrame(performance_data)

def create_tp_confidence_distribution(detailed_df, model_names):
    """
    Analyze the distribution of confidence scores for True Positives ONLY
    """
    all_data = {}
    
    for model_name in model_names:
        confidence_col = f'{model_name}_Confidence'
        
        gt_true_mask = detailed_df['Ground_Truth_Has_Mounting'] == True
        
        tp_detected_confidences = detailed_df[(detailed_df[confidence_col] >= detection_threshold) & gt_true_mask][confidence_col].values
        tp_yolo_detections = detailed_df[(detailed_df[confidence_col] >= confidence_threshold) & gt_true_mask][confidence_col].values
        total_actual_objects = len(detailed_df[gt_true_mask])
        
        counts, _ = np.histogram(tp_yolo_detections, bins=conf_bins)
        
        model_data = {}
        for i in range(len(conf_bins)-1):
            bin_range = f"{conf_bins[i]:.2f}-{conf_bins[i+1]:.2f}"
            model_data[bin_range] = counts[i]
        
        model_data['Total_Actual_Objects'] = total_actual_objects
        model_data['True_Positives_Above_Detection_Threshold'] = len(tp_detected_confidences)
        model_data['True_Positives_Above_YOLO_Threshold'] = len(tp_yolo_detections)
        model_data['Missed_Objects_(False_Negatives)'] = total_actual_objects - len(tp_yolo_detections)
        
        if len(tp_detected_confidences) > 0:
            model_data['Min_Confidence_TP_Detected'] = round(np.min(tp_detected_confidences), 4)
            model_data['Max_Confidence_TP_Detected'] = round(np.max(tp_detected_confidences), 4)
            model_data['Mean_Confidence_TP_Detected'] = round(np.mean(tp_detected_confidences), 4)
            model_data['Median_Confidence_TP_Detected'] = round(np.median(tp_detected_confidences), 4)
        else:
            for k in ['Min_Confidence_TP_Detected', 'Max_Confidence_TP_Detected', 'Mean_Confidence_TP_Detected', 'Median_Confidence_TP_Detected']:
                model_data[k] = 0
            
        if len(tp_yolo_detections) > 0:
            model_data['Min_Confidence_TP_YOLO'] = round(np.min(tp_yolo_detections), 4)
            model_data['Max_Confidence_TP_YOLO'] = round(np.max(tp_yolo_detections), 4)
            model_data['Mean_Confidence_TP_YOLO'] = round(np.mean(tp_yolo_detections), 4)
            model_data['Median_Confidence_TP_YOLO'] = round(np.median(tp_yolo_detections), 4)
        else:
            for k in ['Min_Confidence_TP_YOLO', 'Max_Confidence_TP_YOLO', 'Mean_Confidence_TP_YOLO', 'Median_Confidence_TP_YOLO']:
                model_data[k] = 0
        
        all_data[model_name] = model_data
    
    df = pd.DataFrame(all_data)
    desired_order = [f"{conf_bins[i]:.2f}-{conf_bins[i+1]:.2f}" for i in range(len(conf_bins)-1)]
    desired_order.extend([
        'Total_Actual_Objects', 'True_Positives_Above_Detection_Threshold', 
        'True_Positives_Above_YOLO_Threshold', 'Missed_Objects_(False_Negatives)',
        'Min_Confidence_TP_Detected', 'Max_Confidence_TP_Detected', 
        'Mean_Confidence_TP_Detected', 'Median_Confidence_TP_Detected',
        'Min_Confidence_TP_YOLO', 'Max_Confidence_TP_YOLO',
        'Mean_Confidence_TP_YOLO', 'Median_Confidence_TP_YOLO'
    ])
    
    df = df.reindex(desired_order)
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Metric'}, inplace=True)
    return df

def create_fp_confidence_distribution(detailed_df, model_names):
    """
    Analyze the distribution of confidence scores for False Positives ONLY
    """
    all_data = {}
    
    for model_name in model_names:
        confidence_col = f'{model_name}_Confidence'
        
        gt_false_mask = detailed_df['Ground_Truth_Has_Mounting'] == False
        
        fp_detected_confidences = detailed_df[(detailed_df[confidence_col] >= detection_threshold) & gt_false_mask][confidence_col].values
        fp_yolo_detections = detailed_df[(detailed_df[confidence_col] >= confidence_threshold) & gt_false_mask][confidence_col].values
        total_actual_negatives = len(detailed_df[gt_false_mask])
        
        counts, _ = np.histogram(fp_yolo_detections, bins=conf_bins)
        
        model_data = {}
        for i in range(len(conf_bins)-1):
            bin_range = f"{conf_bins[i]:.2f}-{conf_bins[i+1]:.2f}"
            model_data[bin_range] = counts[i]
        
        model_data['Total_Actual_Negatives'] = total_actual_negatives
        model_data['False_Positives_Above_Detection_Threshold'] = len(fp_detected_confidences)
        model_data['False_Positives_Above_YOLO_Threshold'] = len(fp_yolo_detections)
        model_data['True_Negatives_(Correctly_Ignored)'] = total_actual_negatives - len(fp_yolo_detections)
        
        if len(fp_detected_confidences) > 0:
            model_data['Min_Confidence_FP_Detected'] = round(np.min(fp_detected_confidences), 4)
            model_data['Max_Confidence_FP_Detected'] = round(np.max(fp_detected_confidences), 4)
            model_data['Mean_Confidence_FP_Detected'] = round(np.mean(fp_detected_confidences), 4)
            model_data['Median_Confidence_FP_Detected'] = round(np.median(fp_detected_confidences), 4)
        else:
            for k in ['Min_Confidence_FP_Detected', 'Max_Confidence_FP_Detected', 'Mean_Confidence_FP_Detected', 'Median_Confidence_FP_Detected']:
                model_data[k] = 0
            
        if len(fp_yolo_detections) > 0:
            model_data['Min_Confidence_FP_YOLO'] = round(np.min(fp_yolo_detections), 4)
            model_data['Max_Confidence_FP_YOLO'] = round(np.max(fp_yolo_detections), 4)
            model_data['Mean_Confidence_FP_YOLO'] = round(np.mean(fp_yolo_detections), 4)
            model_data['Median_Confidence_FP_YOLO'] = round(np.median(fp_yolo_detections), 4)
        else:
            for k in ['Min_Confidence_FP_YOLO', 'Max_Confidence_FP_YOLO', 'Mean_Confidence_FP_YOLO', 'Median_Confidence_FP_YOLO']:
                model_data[k] = 0
        
        all_data[model_name] = model_data
    
    df = pd.DataFrame(all_data)
    desired_order = [f"{conf_bins[i]:.2f}-{conf_bins[i+1]:.2f}" for i in range(len(conf_bins)-1)]
    desired_order.extend([
        'Total_Actual_Negatives', 'False_Positives_Above_Detection_Threshold', 
        'False_Positives_Above_YOLO_Threshold', 'True_Negatives_(Correctly_Ignored)',
        'Min_Confidence_FP_Detected', 'Max_Confidence_FP_Detected', 
        'Mean_Confidence_FP_Detected', 'Median_Confidence_FP_Detected',
        'Min_Confidence_FP_YOLO', 'Max_Confidence_FP_YOLO',
        'Mean_Confidence_FP_YOLO', 'Median_Confidence_FP_YOLO'
    ])
    
    df = df.reindex(desired_order)
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'Metric'}, inplace=True)
    return df


def main():
    print("🚀 Starting improved model comparison...")
    
    missing_models = [m for m in models if not os.path.exists(m)]
    if missing_models:
        print("❌ The following model files were not found:")
        for model in missing_models:
            print(f"   - {model}")
        print("Check the paths in the configuration section.")
        return
    
    try:
        os.makedirs(os.path.dirname(excel_output), exist_ok=True)
    except Exception as e:
        print(f"❌ Could not create output directory: {e}")
        return
    
    image_files = collect_images_with_labels(source_dir, labels_dir)
    
    if not image_files:
        print(f"❌ No images with corresponding labels found")
        return
    
    print(f"✓ Working with {len(image_files)} images that have labels")
    
    if not os.path.exists(labels_dir):
        print(f"⚠️  Labels directory not found: {labels_dir}")
        use_ground_truth = False
    else:
        use_ground_truth = True
    
    print("=" * 60)
    if use_ground_truth:
        ground_truth = load_ground_truth_labels(labels_dir, image_files)
        mounting_images = sum(1 for has_mounting in ground_truth.values() if has_mounting)
        print(f"✓ Ground truth loaded: {mounting_images} images with mounting labels")
    else:
        ground_truth = {Path(img).stem: False for img in image_files}
        mounting_images = 0
        print("⚠️  No ground truth available - performance metrics will not be accurate")
    
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
    
    print(f"\n{'='*60}")
    print("ANALYZING RESULTS")
    print(f"{'='*60}")
    
    print("📊 Calculating metrics (background processing)...")
    detailed_df = create_detailed_comparison_table(image_files, model_results, ground_truth, models)
    
    print("📈 Calculating performance metrics...")
    performance_df = calculate_model_performance(detailed_df, model_names)
    
    print("📉 Analyzing confidence distributions...")
    tp_dist_df = create_tp_confidence_distribution(detailed_df, model_names)
    fp_dist_df = create_fp_confidence_distribution(detailed_df, model_names)
    
    print(f"\n{'='*60}")
    print("SAVING RESULTS")
    print(f"{'='*60}")
    print(f"💾 Saving summary to Excel...")
    print(f"📁 File: {excel_output}")
    
    with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
        performance_sorted = performance_df.sort_values('F1_Score', ascending=False)
        performance_sorted.to_excel(writer, sheet_name='Model Performance', index=False)
        
        # Beide distributies als aparte tabbladen
        tp_dist_df.to_excel(writer, sheet_name='TP Confidence Dist', index=False)
        fp_dist_df.to_excel(writer, sheet_name='FP Confidence Dist', index=False)
        
        gt_summary = pd.DataFrame({
            'Metric': ['Total Images', 'Images with Mounting', 'Images without Mounting'],
            'Count': [
                len(ground_truth),
                sum(1 for has_mounting in ground_truth.values() if has_mounting),
                sum(1 for has_mounting in ground_truth.values() if not has_mounting)
            ]
        })
        gt_summary.to_excel(writer, sheet_name='Ground Truth Summary', index=False)
        
        # --- NIEUW: Automatisch de kolombreedte aanpassen voor alle tabbladen ---
        for sheet_name, worksheet in writer.sheets.items():
            for column_cells in worksheet.columns:
                max_length = 0
                col_letter = column_cells[0].column_letter # Haal de letter van de kolom op (bijv. 'A')
                for cell in column_cells:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                # Voeg een klein beetje extra padding toe (bijv. +2) voor de netheid
                adjusted_width = max_length + 2
                worksheet.column_dimensions[col_letter].width = adjusted_width
    
    print("✓ Excel file successfully saved!")
    
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
              f"Accuracy: {row['Accuracy']:.3f} \n"
              f"                Detected (TP+FP): {row['Total_Detections']} | "
              f"TP YOLO Detections: {row['True_Positive_YOLO_Detections']} | "
              f"FN YOLO Detections: {row['False_Negative_YOLO_Detections']}")
    
    best_model = performance_sorted.iloc[0]['Model']
    best_f1 = performance_sorted.iloc[0]['F1_Score']
    print(f"\n🏆 BEST MODEL: {best_model} (F1-Score: {best_f1:.3f})")
    
    print(f"\nSummary results are saved in:")
    print(f"{excel_output}")

if __name__ == "__main__":
    main()
