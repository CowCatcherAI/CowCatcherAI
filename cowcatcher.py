"""
CowCatcher Script
Copyright (C) 2025

This program uses YOLOv11 from Ultralytics (https://github.com/ultralytics/ultralytics)
and is licensed under the terms of the GNU Affero General Public License (AGPL-3.0).

The trained model cowcatcherVx.pt is a derivative work created by training the Ultralytics YOLO framework on a custom dataset.
There are no changes to the original YOLO source code.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This software uses Ultralytics YOLO, available under the AGPL-3.0 license.
The complete source code repository is available at: https://github.com/CowCatcherAI/CowCatcherAI
"""

from ultralytics import YOLO
import cv2
import os
import time
import requests
from datetime import datetime
import config  # Import the config file
from collections import deque

# Configuration for live screen display
SHOW_LIVE_FEED = True  # Set to True to show live screen, False to disable
SEND_ANNOTATED_IMAGES = True  # Set to True to send annotated images, False for original images

print("Script started. Loading YOLO model...")
# Load your trained YOLO model 
model = YOLO(config.MODEL_PATH)
print("YOLO model successfully loaded")

# RTSP URL for the camera - now retrieved from config
rtsp_url_camera1 = config.RTSP_URL_CAMERA1
print(f"Connecting to camera: {rtsp_url_camera1}")

# Folder for saving screenshots
save_folder = "mounting_detections"
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Folder '{save_folder}' created")
else:
    print(f"Folder '{save_folder}' already exists")

# Telegram configuration - now retrieved from config
TELEGRAM_BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = config.TELEGRAM_CHAT_ID

# Test Telegram connection at startup
def test_telegram_connection():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url)
        if response.status_code == 200:
            print("Telegram connection successfully tested.")
            return True
        else:
            print(f"ERROR testing Telegram connection: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR testing Telegram connection: {str(e)}")
        return False

def send_telegram_photo(image_path, caption, disable_notification=False):
    """Sends a photo with caption to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID, 
                'caption': caption,
                'disable_notification': disable_notification
            }
            response = requests.post(url, files=files, data=data)
            
        if response.status_code != 200:
            print(f"ERROR sending Telegram photo: {response.text}")
            return False
            
        return response.json()
    except Exception as e:
        print(f"ERROR sending Telegram photo: {str(e)}")
        return False

def send_telegram_message(message):
    """Sends a text message to Telegram."""
    try:
        url = f"https//api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        response = requests.post(url, data=data)
        
        if response.status_code != 200:
            print(f"ERROR sending Telegram message: {response.text}")
            return False
            
        return response.json()
    except Exception as e:
        print(f"ERROR sending Telegram message: {str(e)}")
        return False

# Test Telegram connection
if not test_telegram_connection():
    print("Telegram connection failed, script will exit.")
    exit()

# Open the camera stream
print("Opening camera stream...")
cap = cv2.VideoCapture(rtsp_url_camera1)
if not cap.isOpened():
    print("ERROR: Cannot open camera stream")
    exit()
else:
    print("Camera stream successfully opened")
    print(f"Live display is {'enabled' if SHOW_LIVE_FEED else 'disabled'}")

# Constants for detection
SAVE_THRESHOLD = 0.7      # Threshold for saving images
NOTIFY_THRESHOLD = 0.84   # Threshold for sending notifications
PEAK_DETECTION_THRESHOLD = 0.89  # Threshold for peak detection
MAX_SCREENSHOTS = 2       # Number of screenshots to send per event - adjusted to 1
COLLECTION_TIME = 50      # Maximum time to collect screenshots in seconds (increased to 60s)
MIN_COLLECTION_TIME = 4   # Minimum time to collect, even after peak detection
INACTIVITY_STOP_TIME = 6  # Stops collecting after 6 seconds without detections above SAVE_THRESHOLD
MIN_HIGH_CONFIDENCE_DETECTIONS = 3  # NEW: Minimum required detections above NOTIFY_THRESHOLD
frame_count = 0
process_every_n_frames = 2  # Process every 2 frames
last_detection_time = None
cooldown_period = 40  # Seconds between consecutive notifications

# NEW: Variables for sound notifications
notification_counter = 0  # Counter for notifications
SOUND_EVERY_N_NOTIFICATIONS = 5  # Sound every 5th notification

# New: Deque for tracking confidence score progression
confidence_history = deque(maxlen=10)  # Keep last 10 confidence scores (shorter for fast events)
frame_history = deque(maxlen=10)       # Keep corresponding frames
timestamp_history = deque(maxlen=10)   # Keep corresponding timestamps

# Variables for collecting the best screenshots during an event
collecting_screenshots = False
collection_start_time = None
event_detections = []     # List of tuples (confidence, frame, timestamp, original_image_path, results_obj)
peak_detected = False     # Indicator if a peak was detected
last_detection_time = None  # Last time there was a detection above SAVE_THRESHOLD
inactivity_period = 0     # Track how long there has been no activity

print(f"Processing started, every {process_every_n_frames} frames will be analyzed")
print(f"Image save threshold: {SAVE_THRESHOLD}")
print(f"Notification send threshold: {NOTIFY_THRESHOLD}")
print(f"Peak detection threshold: {PEAK_DETECTION_THRESHOLD}")
print(f"Maximum {MAX_SCREENSHOTS} screenshots per event")
print(f"Collection time: {MIN_COLLECTION_TIME}-{COLLECTION_TIME} seconds")
print(f"Stops automatically after {INACTIVITY_STOP_TIME} seconds of inactivity")
print(f"Minimum {MIN_HIGH_CONFIDENCE_DETECTIONS} detections above {NOTIFY_THRESHOLD} required for notification")  # NEW: Log the new setting
print(f"Telegram images: {'With bounding boxes' if SEND_ANNOTATED_IMAGES else 'Without bounding boxes'}")
print(f"Sound notification every {SOUND_EVERY_N_NOTIFICATIONS} alerts")  # NEW: Log sound setting

# Send a start message to confirm everything is working
start_message = f"📋 Cowcatcher detection script started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n⚠️ DISCLAIMER: Use at your own risk. This program uses Ultralytics YOLO and is subject to the GNU Affero General Public License v3.0 (AGPL-3.0)."
send_telegram_message(start_message)

def detect_mounting_peak(confidence_history, frame_history, timestamp_history):
    """
    Detects the peak of a mounting event based on confidence score progression.
    Returns a tuple with (peak_index, peak_confidence, before_peak_index, after_peak_index)
    """
    if len(confidence_history) < 5:  # We need at least 5 data points
        return None, None, None, None
    
    # Find the highest confidence score
    max_conf = max(confidence_history)
    max_idx = confidence_history.index(max_conf)
    
    # If the maximum confidence is below our peak threshold, this is not a clear peak moment
    if max_conf < PEAK_DETECTION_THRESHOLD:
        return None, None, None, None
    
    # Find a frame from just before the peak (for context)
    before_peak_idx = max(0, max_idx - 2)
    
    # Find a frame from just after the peak (to see the decline)
    after_peak_idx = min(len(confidence_history) - 1, max_idx + 2)
    
    # Return information about the peak and surrounding frames
    return max_idx, before_peak_idx, after_peak_idx, max_conf

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Cannot read frame from camera")
            # Try to reconnect to the camera
            cap.release()
            time.sleep(5)
            cap = cv2.VideoCapture(rtsp_url_camera1)
            continue
            
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Frames processed: {frame_count}")
        
        # Only process every n frames
        if frame_count % process_every_n_frames == 0:
            # Perform detection
            results = model.predict(source=frame, classes=[0], conf=0.2, verbose=False)
            
            # Find highest confidence detection
            highest_conf_detection = None
            highest_conf = 0.0
            if len(results[0].boxes) > 0:
                # Sort detections by confidence (highest first)
                sorted_detections = sorted(results[0].boxes, key=lambda x: float(x.conf), reverse=True)
                if len(sorted_detections) > 0:
                    highest_conf_detection = sorted_detections[0]
                    highest_conf = float(highest_conf_detection.conf)
            
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            # Save detection in history (even at low confidence to see progression)
            if highest_conf_detection is not None:
                confidence_history.append(highest_conf)
                frame_history.append(frame.copy())  # Save a copy of the frame
                timestamp_history.append(timestamp)
            else:
                # Add zero if there's no detection (important for detecting progression)
                confidence_history.append(0.0)
                frame_history.append(frame.copy())
                timestamp_history.append(timestamp)
                
            can_send_notification = (last_detection_time is None or 
                                    (current_time - last_detection_time).total_seconds() > cooldown_period)
            
            # Start collecting screenshots if we have a detection above SAVE_THRESHOLD
            if highest_conf >= SAVE_THRESHOLD and not collecting_screenshots and can_send_notification:
                print(f"Starting screenshot collection for {COLLECTION_TIME} seconds (searching for peak moment)")
                collecting_screenshots = True
                collection_start_time = current_time
                event_detections = []
                peak_detected = False
                
                # Add any previous frames that are already in history (for context)
                for i in range(len(confidence_history)):
                    if confidence_history[i] >= SAVE_THRESHOLD:
                        # Get historical frame
                        hist_frame = frame_history[i]
                        hist_timestamp = timestamp_history[i]
                        hist_conf = confidence_history[i]
                        
                        # Save the original frame
                        hist_original_save_path = os.path.join(save_folder, f"mounting_detected{hist_timestamp}_conf{hist_conf:.2f}_history.jpg")
                        cv2.imwrite(hist_original_save_path, hist_frame)
                        
                        # We don't have a result object for historical frames, so make a simple annotation
                        hist_annotated_frame = hist_frame.copy()
                        cv2.putText(hist_annotated_frame, f"Conf: {hist_conf:.2f}", (10, 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # Add to event_detections (without result object, with annotated frame)
                        if SHOW_LIVE_FEED:
                            event_detections.append((hist_conf, hist_annotated_frame, hist_timestamp, hist_original_save_path, None))
                        else:
                            event_detections.append((hist_conf, None, hist_timestamp, hist_original_save_path, None))
                
            # If we are collecting
            if collecting_screenshots:
                # If there's a detection, add to collection
                if highest_conf_detection is not None and highest_conf >= SAVE_THRESHOLD:
                    # Save original frame
                    original_save_path = os.path.join(save_folder, f"mounting_detected_{timestamp}_conf{highest_conf:.2f}.jpg")
                    cv2.imwrite(original_save_path, frame)
                    
                    # Make annotated frame for live display, but don't save it yet
                    annotated_frame = results[0].plot()
                    
                    # Add to collection - with annotated_frame for live display and results[0] for later annotations
                    if SHOW_LIVE_FEED:
                        event_detections.append((highest_conf, annotated_frame.copy(), timestamp, original_save_path, results[0]))
                    else:
                        event_detections.append((highest_conf, None, timestamp, original_save_path, results[0]))
                    
                    print(f"Detection added to collection: {highest_conf:.2f}")
                    
                    # Reset inactivity period when we have a detection above SAVE_THRESHOLD
                    inactivity_period = 0
                    last_detection_time = current_time
                    
                    # Check if we have detected a peak
                    if highest_conf >= PEAK_DETECTION_THRESHOLD and not peak_detected:
                        peak_detected = True
                        print(f"Possible peak detected with confidence {highest_conf:.2f}")
                else:
                    # If there's no detection above SAVE_THRESHOLD, increase inactivity period
                    if last_detection_time is not None:
                        inactivity_period = (current_time - last_detection_time).total_seconds()
                        if inactivity_period >= 2:  # Log every 2 seconds
                            print(f"Inactivity period: {inactivity_period:.1f}s")
                
                # Check if we should stop collecting
                collection_duration = (current_time - collection_start_time).total_seconds()
                
                # Stop collecting if:
                # 1. We had a peak moment and minimum collection time has passed, or
                # 2. We reached maximum collection time, or
                # 3. We have a very clear detection (above 0.85) - immediate response for clear cases, or
                # 4. The inactivity period has reached INACTIVITY_STOP_TIME (no detections for X seconds)
                if (peak_detected and collection_duration >= MIN_COLLECTION_TIME) or \
                   collection_duration >= COLLECTION_TIME or \
                   (highest_conf >= 0.85 and collection_duration >= 1) or \
                   inactivity_period >= INACTIVITY_STOP_TIME:
                    # Time to stop collecting and determine which images to send
                    print(f"Collection stopped after {collection_duration:.1f} seconds with {len(event_detections)} detections")
                    
                    # Find the peak moment in the collected data
                    current_confidences = [conf for conf, _, _, _, _ in event_detections]
                    
                    # NEW: Check if there are enough detections above NOTIFY_THRESHOLD
                    high_conf_detections = sum(1 for conf in current_confidences if conf >= NOTIFY_THRESHOLD)
                    print(f"Number of high confidence detections: {high_conf_detections}/{MIN_HIGH_CONFIDENCE_DETECTIONS} required")
                    
                    # For short events: even with few detections, still send a notification
                    if len(current_confidences) > 0:
                        # Find the highest confidence and index
                        max_conf = max(current_confidences)
                        max_idx = current_confidences.index(max_conf)
                        
                        # Determine which images we want to send
                        selected_indices = []
                        
                        # For very short events with few frames
                        if len(current_confidences) <= 2:
                            # If we only have 1 or 2 frames, just send them all
                            selected_indices = list(range(len(current_confidences)))
                        else:
                            # For longer events: try to select before, peak, and after
                            # Add the peak
                            selected_indices.append(max_idx)
                            
                            # Try to add an image before the peak - if it exists
                            if max_idx > 0:
                                selected_indices.append(max(0, max_idx - 1))  # Directly before the peak
                            
                            # Try to add an image after the peak - if it exists
                            if max_idx < len(event_detections) - 1:
                                selected_indices.append(max_idx + 1)  # Directly after the peak
                        
                        # Sort and limit to MAX_SCREENSHOTS
                        selected_indices = sorted(selected_indices)[:MAX_SCREENSHOTS]
                        
                        # MODIFIED: Send the selected images if we have both sufficient confidence
                        # and sufficient detections above the threshold
                        if max_conf >= NOTIFY_THRESHOLD and high_conf_detections >= MIN_HIGH_CONFIDENCE_DETECTIONS:
                            # NEW: Increment the notification counter
                            notification_counter += 1
                            
                            # NEW: Determine if sound should play (every 5th notification)
                            play_sound = (notification_counter % SOUND_EVERY_N_NOTIFICATIONS == 0)
                            
                            for rank, idx in enumerate(selected_indices):
                                conf, img, ts, original_path, results_obj = event_detections[idx]
                                
                                # For very short events (with 1-2 frames), use simpler labels
                                if len(selected_indices) <= 2:
                                    stage = "Best capture" if idx == max_idx else "Extra capture"
                                else:
                                    # Determine stage (before peak, peak, after peak)
                                    stage = "Before peak" if idx < max_idx else "Peak" if idx == max_idx else "After peak"
                                
                                # Determine which path to use based on configuration
                                if SEND_ANNOTATED_IMAGES:
                                    # We need to save the annotated version for sending
                                    annotated_save_path = os.path.join(save_folder, f"mounting_detected_{ts}_conf{conf:.2f}_annotated.jpg")
                                    
                                    # If the annotated image is already made (via live view), use it
                                    if img is not None:
                                        # Save the image that's already in memory
                                        cv2.imwrite(annotated_save_path, img)
                                        send_path = annotated_save_path
                                    # Otherwise, if we have a result object, make a new annotation
                                    elif results_obj is not None:
                                        # Load the original frame
                                        orig_frame = cv2.imread(original_path)
                                        if orig_frame is not None:
                                            # Make a new annotation with the result object
                                            annotated_frame = results_obj.plot()
                                            # Save the annotated version
                                            cv2.imwrite(annotated_save_path, annotated_frame)
                                            send_path = annotated_save_path
                                        else:
                                            # Fallback if the original frame cannot be loaded
                                            print(f"Could not load original frame for {original_path}, sending original")
                                            send_path = original_path
                                    else:
                                        # Fallback if we can't make an annotated version
                                        print(f"No result object available for {ts}, sending original")
                                        send_path = original_path
                                else:
                                    # Use the original path without annotations
                                    send_path = original_path
                                
                                # NEW: Message for Telegram with sound indicator
                                sound_indicator = "🔊" if play_sound else "🔇"
                                message = f"{sound_indicator} Mounting detected ({ts}) - Confidence: {conf:.2f}\n"
                                message += f"Stage: {stage} - Rank {rank+1}/{len(selected_indices)}\n"
                                message += f"Event duration: {collection_duration:.1f}s\n"

                                
                                # NEW: Send to Telegram (sound off except for every 5th notification)
                                response = send_telegram_photo(send_path, message, disable_notification=not play_sound)
                                if response:
                                    sound_status = "WITH sound" if play_sound else "without sound"
                                    print(f"Telegram message sent for {stage}: {conf:.2f} "
                                          f"({'with' if SEND_ANNOTATED_IMAGES and send_path != original_path else 'without'} bounding boxes) - {sound_status}")
                                else:
                                    print(f"Telegram message sending failed for {stage}")
                            
                            # Set last detection time for cooldown
                            last_detection_time = current_time
                            print(f"Cooldown period of {cooldown_period} seconds started")
                            # NEW: Log sound status
                            if play_sound:
                                print(f"🔊 SOUND NOTIFICATION #{notification_counter} sent!")
                            else:
                                print(f"🔇 Silent notification #{notification_counter} sent (sound every {SOUND_EVERY_N_NOTIFICATIONS})")
                        else:
                            # MODIFIED: Give clear reason why no notification was sent
                            if max_conf < NOTIFY_THRESHOLD:
                                print(f"Highest confidence ({max_conf:.2f}) lower than NOTIFY_THRESHOLD ({NOTIFY_THRESHOLD}). No notification sent.")
                            elif high_conf_detections < MIN_HIGH_CONFIDENCE_DETECTIONS:
                                print(f"Too few high confidence detections ({high_conf_detections}/{MIN_HIGH_CONFIDENCE_DETECTIONS}). No notification sent.")
                    
                    # Reset collection status
                    collecting_screenshots = False
                    peak_detected = False
                    inactivity_period = 0
                    
                    # Log reason for stopping collection
                    if inactivity_period >= INACTIVITY_STOP_TIME:
                        print(f"Collection stopped due to inactivity ({inactivity_period:.1f}s without detections)")
                    elif highest_conf >= 0.85 and collection_duration >= 1:
                        print(f"Collection stopped due to very high confidence detection ({highest_conf:.2f})")
                    elif peak_detected and collection_duration >= MIN_COLLECTION_TIME:
                        print(f"Collection stopped after peak detection and minimum collection time ({collection_duration:.1f}s)")
                    else:
                        print(f"Collection stopped after maximum collection time ({collection_duration:.1f}s)")
            
            # Show the frame with detections only if SHOW_LIVE_FEED is enabled
            if SHOW_LIVE_FEED and len(results) > 0:  # Check if there are results
                annotated_frame = results[0].plot()
                cv2.imshow("Cowcatcher Detection", annotated_frame)
        
        # Key press to stop (q), but only check if the window is open
        if SHOW_LIVE_FEED and (cv2.waitKey(1) & 0xFF == ord('q')):
            print("User pressed 'q'. Script will stop.")
            break

except KeyboardInterrupt:
    print("Script stopped by user (Ctrl+C)")
    stop_reason = "Script manually stopped by user (Ctrl+C)"
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    stop_reason = f"Script stopped due to error: {str(e)}"
    
finally:
    # Cleanup
    cap.release()
    if SHOW_LIVE_FEED:
        cv2.destroyAllWindows()
    print("Camera stream closed and resources released")
    print(f"Total frames processed: {frame_count}")
    
    # Send a message that the script has stopped
    stop_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if 'stop_reason' not in locals():
        stop_reason = "Script stopped (reason unknown)"
    
    stop_message = f"⚠️ WARNING: Cowcatcher detection script stopped at {stop_time}\n"
    stop_message += f"Reason: {stop_reason}\n"
    stop_message += f"Total frames processed: {frame_count}\n"
    stop_message += f"Total notifications sent: {notification_counter}"  # NEW: Show total notification count
    
    send_telegram_message(stop_message)
    print(f"Stop message sent to Telegram")


