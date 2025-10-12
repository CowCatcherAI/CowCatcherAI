"""
Copyright (C) 2025
latest adjustment 9-october-2025

This program uses YOLOv12 from Ultralytics (https://github.com/ultralytics/ultralytics)
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
import sys
import time
import requests
import glob
from datetime import datetime
from collections import deque
from threading import Thread
from queue import Queue

# Setup logging to both console and file
import logging

# Use Docker path if running in container, otherwise use local path
DATA_DIR = '/app/data' if os.path.exists('/app') else './data'
LOG_FILE = os.path.join(DATA_DIR, 'cowcatcher.log')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Status file for web UI
STATUS_FILE = os.path.join(DATA_DIR, 'status.json')

def update_status(component, status, message=""):
    """Update component status for web UI monitoring"""
    try:
        import json
        status_data = {}
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                status_data = json.load(f)
        
        status_data[component] = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        logger.debug(f"Could not update status file: {e}")

# Load configuration from JSON file
import config_loader
config_data = config_loader.get_config()

# Configuration for live screen display
SHOW_LIVE_FEED = config_data.get('show_live_feed', False)
SEND_ANNOTATED_IMAGES = config_data.get('send_annotated_images', True)
CAMERA_NAME = config_data.get('camera_name', 'Camera 1')

logger.info("Script started. Loading YOLO model...")
MODEL_PATH = config_data['model_path']

# Check if model file exists, fallback to standard YOLO if not
if not os.path.exists(MODEL_PATH):
    logger.warning(f"Custom model {MODEL_PATH} not found. Falling back to yolov8n.pt")
    MODEL_PATH = "yolov8n.pt"  # This will auto-download if not present

try:
    model = YOLO(MODEL_PATH, task='detect')
    logger.info(f"YOLO model successfully loaded: {MODEL_PATH}")
    update_status('yolo', 'ok', f"Model loaded: {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}")
    logger.info("Attempting to load fallback model yolov8n.pt...")
    model = YOLO("yolov8n.pt", task='detect')
    logger.info("Fallback YOLO model successfully loaded")
    update_status('yolo', 'ok', "Fallback model loaded: yolov8n.pt")

# Get video source - either RTSP URL or video file
developer_mode = config_data.get('developer_mode', False)
use_video_file = config_data.get('use_video_file', False)

if developer_mode and use_video_file:
    video_source = config_data.get('video_file_path', '')
    logger.info(f"Developer mode: Using video file: {video_source}")
else:
    video_source = config_data.get('rtsp_url', config_data.get('rtsp_url_camera1', ''))
    logger.info(f"Connecting to camera: {video_source}")

# Legacy support
rtsp_url_camera1 = video_source

# Folder for saving screenshots - use Docker path if in container, otherwise local
save_folder = os.path.join(DATA_DIR, "mounting_detections")
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    logger.info(f"Folder '{save_folder}' created")
else:
    logger.info(f"Folder '{save_folder}' already exists")

# Function to cleanup old detections
def cleanup_old_detections():
    """Remove old detection files beyond the configured limit"""
    try:
        max_keep = config_data.get('max_detections_to_keep', 500)
        files = glob.glob(os.path.join(save_folder, '*.jpg'))
        
        if len(files) <= max_keep:
            return
        
        # Sort by modification time (oldest first)
        files.sort(key=os.path.getmtime)
        
        # Remove oldest files
        files_to_remove = files[:len(files) - max_keep]
        removed = 0
        for filepath in files_to_remove:
            try:
                os.remove(filepath)
                removed += 1
            except Exception as e:
                logger.error(f"Error removing {filepath}: {e}")
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old detection file(s)")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Telegram configuration - MULTI-CHAT SUPPORT
TELEGRAM_BOT_TOKEN = config_data['telegram_bot_token']
TELEGRAM_CHAT_IDS = config_data['telegram_chat_ids']

logger.info(f"Telegram configured for {len(TELEGRAM_CHAT_IDS)} chat(s)")

# THREADING SETUP FOR TELEGRAM
telegram_queue = Queue()
telegram_stats = {'sent': 0, 'failed': 0}

def telegram_worker():
    """Background thread that processes Telegram tasks"""
    while True:
        try:
            task = telegram_queue.get()
            
            if task is None:  # Stop signal
                break
            
            task_type, *args = task
            
            if task_type == 'photo':
                image_path, caption, disable_notification = args
                result = _send_telegram_photo_sync(image_path, caption, disable_notification)
                telegram_stats['sent' if result else 'failed'] += 1
                    
            elif task_type == 'message':
                message = args[0]
                result = _send_telegram_message_sync(message)
                telegram_stats['sent' if result else 'failed'] += 1
            
            telegram_queue.task_done()
            
        except Exception as e:
            logger.info(f"ERROR in telegram worker: {str(e)}")

def _send_telegram_photo_sync(image_path, caption, disable_notification=False):
    """Internal synchronous photo sender (runs in background thread) - sends to all chat IDs"""
    success_count = 0
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'disable_notification': disable_notification
                }
                response = requests.post(url, files=files, data=data, timeout=30)
                
            if response.status_code != 200:
                logger.info(f"ERROR sending Telegram photo to chat {chat_id}: {response.text}")
            else:
                success_count += 1
                
        except Exception as e:
            logger.info(f"ERROR sending Telegram photo to chat {chat_id}: {str(e)}")
    
    return success_count > 0

def _send_telegram_message_sync(message):
    """Internal synchronous message sender (runs in background thread) - sends to all chat IDs"""
    success_count = 0
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {'chat_id': chat_id, 'text': message}
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code != 200:
                logger.info(f"ERROR sending Telegram message to chat {chat_id}: {response.text}")
            else:
                success_count += 1
                
        except Exception as e:
            logger.info(f"ERROR sending Telegram message to chat {chat_id}: {str(e)}")
    
    return success_count > 0

def send_telegram_photo(image_path, caption, disable_notification=False):
    """Queue photo for sending (returns immediately)"""
    if 'telegram_available' in globals() and telegram_available:
        telegram_queue.put(('photo', image_path, caption, disable_notification))
        return True
    else:
        logger.debug("Telegram not available, skipping photo send")
        return False

def send_telegram_message(message):
    """Queue message for sending (returns immediately)"""
    if 'telegram_available' in globals() and telegram_available:
        telegram_queue.put(('message', message))
        return True
    else:
        logger.debug("Telegram not available, skipping message send")
        return False
# END THREADING SETUP

def test_telegram_connection():
    """Test Telegram connection at startup - tests all chat IDs"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram bot connection successfully tested.")
            
            # Test each chat ID
            valid_chats = []
            for chat_id in TELEGRAM_CHAT_IDS:
                try:
                    test_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChat"
                    test_response = requests.get(test_url, params={'chat_id': chat_id}, timeout=10)
                    if test_response.status_code == 200:
                        valid_chats.append(chat_id)
                        logger.info(f"  ✓ Chat ID {chat_id} is valid")
                    else:
                        logger.info(f"  ✗ Chat ID {chat_id} is invalid: {test_response.text}")
                except Exception as e:
                    logger.info(f"  ✗ Could not verify chat ID {chat_id}: {str(e)}")
            
            if len(valid_chats) == 0:
                logger.info("ERROR: No valid chat IDs found!")
                return False
            
            logger.info(f"Successfully configured {len(valid_chats)}/{len(TELEGRAM_CHAT_IDS)} chat(s)")
            return True
        else:
            logger.info(f"ERROR testing Telegram connection: {response.text}")
            return False
    except Exception as e:
        logger.info(f"ERROR testing Telegram connection: {str(e)}")
        return False

# Test Telegram connection
telegram_available = test_telegram_connection()
if not telegram_available:
    logger.warning("Telegram connection failed, continuing without Telegram notifications. Configure Telegram in the web UI.")
    update_status('telegram', 'error', "Connection failed - check bot token and chat IDs")
else:
    # Start Telegram worker thread only if connection is successful
    telegram_thread = Thread(target=telegram_worker, daemon=True)
    telegram_thread.start()
    logger.info("Telegram worker thread started (async mode enabled)")
    update_status('telegram', 'ok', "Connected and ready")

# Open the camera stream
logger.info("Opening camera stream...")
cap = cv2.VideoCapture(rtsp_url_camera1)
camera_available = cap.isOpened()
if not camera_available:
    logger.warning("Cannot open camera stream, continuing without camera input. Configure camera in the web UI.")
    cap = None
    update_status('camera', 'error', f"Cannot connect to: {rtsp_url_camera1}")
else:
    logger.info("Camera stream successfully opened")
    logger.info(f"Live display is {'enabled' if SHOW_LIVE_FEED else 'disabled'}")
    update_status('camera', 'ok', f"Connected to: {CAMERA_NAME}")

# Constants for detection - load from config
SAVE_THRESHOLD = config_data.get('save_threshold', 0.75)
NOTIFY_THRESHOLD = config_data.get('notify_threshold', 0.86)
PEAK_DETECTION_THRESHOLD = config_data.get('peak_detection_threshold', 0.89)
MAX_SCREENSHOTS = config_data.get('max_screenshots', 2)
COLLECTION_TIME = config_data.get('collection_time', 50)
MIN_COLLECTION_TIME = config_data.get('min_collection_time', 4)
INACTIVITY_STOP_TIME = config_data.get('inactivity_stop_time', 6)
MIN_HIGH_CONFIDENCE_DETECTIONS = config_data.get('min_high_confidence_detections', 3)
cooldown_period = config_data.get('cooldown_period', 40)
SOUND_EVERY_N_NOTIFICATIONS = config_data.get('sound_every_n_notifications', 5)

# Config reload tracking
last_config_check = time.time()
CONFIG_RELOAD_INTERVAL = 30  # Check for config updates every 30 seconds

def reload_config_if_needed():
    """Reload configuration settings that can be updated without restarting"""
    global SAVE_THRESHOLD, NOTIFY_THRESHOLD, PEAK_DETECTION_THRESHOLD
    global MAX_SCREENSHOTS, COLLECTION_TIME, MIN_COLLECTION_TIME
    global INACTIVITY_STOP_TIME, MIN_HIGH_CONFIDENCE_DETECTIONS
    global cooldown_period, SOUND_EVERY_N_NOTIFICATIONS
    global last_config_check, SEND_ANNOTATED_IMAGES
    
    current_time = time.time()
    if current_time - last_config_check < CONFIG_RELOAD_INTERVAL:
        return False
    
    last_config_check = current_time
    
    try:
        new_config = config_loader.get_config()
        
        # Update thresholds and settings
        SAVE_THRESHOLD = new_config.get('save_threshold', 0.75)
        NOTIFY_THRESHOLD = new_config.get('notify_threshold', 0.86)
        PEAK_DETECTION_THRESHOLD = new_config.get('peak_detection_threshold', 0.89)
        MAX_SCREENSHOTS = new_config.get('max_screenshots', 2)
        COLLECTION_TIME = new_config.get('collection_time', 50)
        MIN_COLLECTION_TIME = new_config.get('min_collection_time', 4)
        INACTIVITY_STOP_TIME = new_config.get('inactivity_stop_time', 6)
        MIN_HIGH_CONFIDENCE_DETECTIONS = new_config.get('min_high_confidence_detections', 3)
        cooldown_period = new_config.get('cooldown_period', 40)
        SOUND_EVERY_N_NOTIFICATIONS = new_config.get('sound_every_n_notifications', 5)
        SEND_ANNOTATED_IMAGES = new_config.get('send_annotated_images', True)
        
        logger.info("Configuration reloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        return False


frame_count = 0
process_every_n_frames = 2  # Process every 2 frames
last_detection_time = None

notification_counter = 0

confidence_history = deque(maxlen=10)
frame_history = deque(maxlen=10)
timestamp_history = deque(maxlen=10)

collecting_screenshots = False
collection_start_time = None
event_detections = []
peak_detected = False
inactivity_period = 0

logger.info(f"Processing started, every {process_every_n_frames} frames will be analyzed")
logger.info(f"Image save threshold: {SAVE_THRESHOLD}")
logger.info(f"Notification send threshold: {NOTIFY_THRESHOLD}")
logger.info(f"Peak detection threshold: {PEAK_DETECTION_THRESHOLD}")
logger.info(f"Maximum {MAX_SCREENSHOTS} screenshots per event")
logger.info(f"Collection time: {MIN_COLLECTION_TIME}-{COLLECTION_TIME} seconds")
logger.info(f"Stops automatically after {INACTIVITY_STOP_TIME} seconds of inactivity")
logger.info(f"Minimum {MIN_HIGH_CONFIDENCE_DETECTIONS} detections above {NOTIFY_THRESHOLD} required for notification")
logger.info(f"Telegram images: {'With bounding boxes' if SEND_ANNOTATED_IMAGES else 'Without bounding boxes'}")
logger.info(f"Sound notification every {SOUND_EVERY_N_NOTIFICATIONS} alerts")

start_message = f"📋 Cowcatcher detection script started\n"
start_message += f"Camera: {CAMERA_NAME}\n"
start_message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
start_message += f"⚠️ DISCLAIMER: Use at your own risk. This program uses Ultralytics YOLO and is subject to the GNU Affero General Public License v3.0 (AGPL-3.0)."
send_telegram_message(start_message)

def detect_mounting_peak(confidence_history, frame_history, timestamp_history):
    """Detects the peak of a mounting event based on confidence score progression."""
    if len(confidence_history) < 5:
        return None, None, None, None
    
    max_conf = max(confidence_history)
    max_idx = confidence_history.index(max_conf)
    
    if max_conf < PEAK_DETECTION_THRESHOLD:
        return None, None, None, None
    
    before_peak_idx = max(0, max_idx - 2)
    after_peak_idx = min(len(confidence_history) - 1, max_idx + 2)
    
    return max_idx, before_peak_idx, after_peak_idx, max_conf

try:
    # Mark system as running
    update_status('system', 'running', "CowCatcher detection system is active")
    
    while True:
        # If camera is not available, just wait and check for config changes
        if cap is None or not camera_available:
            update_status('camera', 'error', f"Disconnected - attempting reconnection")
            time.sleep(5)
            reload_config_if_needed()
            # Try to reconnect to camera if config changed
            cap = cv2.VideoCapture(rtsp_url_camera1)
            camera_available = cap.isOpened()
            if camera_available:
                logger.info("Camera connection restored!")
                update_status('camera', 'ok', f"Connection restored: {CAMERA_NAME}")
            continue
            
        ret, frame = cap.read()
        if not ret:
            logger.warning("Cannot read frame from camera, attempting to reconnect...")
            cap.release()
            camera_available = False
            cap = None
            continue
            
        frame_count += 1
        
        # Periodically reload configuration
        reload_config_if_needed()
        
        if frame_count % 100 == 0:
            logger.info(f"Frames processed: {frame_count} | Queue: {telegram_queue.qsize()} | Sent: {telegram_stats['sent']} | Failed: {telegram_stats['failed']}")
        
        if frame_count % process_every_n_frames == 0:
            results = model.predict(source=frame, classes=[0], conf=0.2, verbose=False)
            
            highest_conf_detection = None
            highest_conf = 0.0
            if len(results[0].boxes) > 0:
                sorted_detections = sorted(results[0].boxes, key=lambda x: float(x.conf), reverse=True)
                if len(sorted_detections) > 0:
                    highest_conf_detection = sorted_detections[0]
                    highest_conf = float(highest_conf_detection.conf)
            
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            if highest_conf_detection is not None:
                confidence_history.append(highest_conf)
                frame_history.append(frame.copy())
                timestamp_history.append(timestamp)
            else:
                confidence_history.append(0.0)
                frame_history.append(frame.copy())
                timestamp_history.append(timestamp)
                
            can_send_notification = (last_detection_time is None or 
                                    (current_time - last_detection_time).total_seconds() > cooldown_period)
            
            if highest_conf >= SAVE_THRESHOLD and not collecting_screenshots and can_send_notification:
                logger.info(f"Starting screenshot collection for {COLLECTION_TIME} seconds (searching for peak moment)")
                collecting_screenshots = True
                collection_start_time = current_time
                event_detections = []
                peak_detected = False
                
                for i in range(len(confidence_history)):
                    if confidence_history[i] >= SAVE_THRESHOLD:
                        hist_frame = frame_history[i]
                        hist_timestamp = timestamp_history[i]
                        hist_conf = confidence_history[i]
                        
                        hist_original_save_path = os.path.join(save_folder, f"mounting_detected{hist_timestamp}_conf{hist_conf:.2f}_history.jpg")
                        cv2.imwrite(hist_original_save_path, hist_frame)
                        
                        hist_annotated_frame = hist_frame.copy()
                        cv2.putText(hist_annotated_frame, f"Conf: {hist_conf:.2f}", (10, 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        if SHOW_LIVE_FEED:
                            event_detections.append((hist_conf, hist_annotated_frame, hist_timestamp, hist_original_save_path, None))
                        else:
                            event_detections.append((hist_conf, None, hist_timestamp, hist_original_save_path, None))
                
            if collecting_screenshots:
                if highest_conf_detection is not None and highest_conf >= SAVE_THRESHOLD:
                    original_save_path = os.path.join(save_folder, f"mounting_detected_{timestamp}_conf{highest_conf:.2f}.jpg")
                    cv2.imwrite(original_save_path, frame)
                    
                    annotated_frame = results[0].plot()
                    
                    if SHOW_LIVE_FEED:
                        event_detections.append((highest_conf, annotated_frame.copy(), timestamp, original_save_path, results[0]))
                    else:
                        event_detections.append((highest_conf, None, timestamp, original_save_path, results[0]))
                    
                    logger.info(f"Detection added to collection: {highest_conf:.2f}")
                    
                    inactivity_period = 0
                    last_detection_time = current_time
                    
                    if highest_conf >= PEAK_DETECTION_THRESHOLD and not peak_detected:
                        peak_detected = True
                        logger.info(f"Possible peak detected with confidence {highest_conf:.2f}")
                else:
                    if last_detection_time is not None:
                        inactivity_period = (current_time - last_detection_time).total_seconds()
                        if inactivity_period >= 2:
                            logger.info(f"Inactivity period: {inactivity_period:.1f}s")
                
                collection_duration = (current_time - collection_start_time).total_seconds()
                
                if (peak_detected and collection_duration >= MIN_COLLECTION_TIME) or \
                   collection_duration >= COLLECTION_TIME or \
                   (highest_conf >= 0.85 and collection_duration >= 1) or \
                   inactivity_period >= INACTIVITY_STOP_TIME:
                    
                    logger.info(f"Collection stopped after {collection_duration:.1f} seconds with {len(event_detections)} detections")
                    
                    current_confidences = [conf for conf, _, _, _, _ in event_detections]
                    high_conf_detections = sum(1 for conf in current_confidences if conf >= NOTIFY_THRESHOLD)
                    logger.info(f"Number of high confidence detections: {high_conf_detections}/{MIN_HIGH_CONFIDENCE_DETECTIONS} required")
                    
                    if len(current_confidences) > 0:
                        max_conf = max(current_confidences)
                        max_idx = current_confidences.index(max_conf)
                        
                        selected_indices = []
                        
                        if len(current_confidences) <= 2:
                            selected_indices = list(range(len(current_confidences)))
                        else:
                            selected_indices.append(max_idx)
                            if max_idx > 0:
                                selected_indices.append(max(0, max_idx - 1))
                            if max_idx < len(event_detections) - 1:
                                selected_indices.append(max_idx + 1)
                        
                        selected_indices = sorted(selected_indices)[:MAX_SCREENSHOTS]
                        
                        if max_conf >= NOTIFY_THRESHOLD and high_conf_detections >= MIN_HIGH_CONFIDENCE_DETECTIONS:
                            notification_counter += 1
                            play_sound = (notification_counter % SOUND_EVERY_N_NOTIFICATIONS == 0)
                            
                            for rank, idx in enumerate(selected_indices):
                                conf, img, ts, original_path, results_obj = event_detections[idx]
                                
                                if len(selected_indices) <= 2:
                                    stage = "Best capture" if idx == max_idx else "Extra capture"
                                else:
                                    stage = "Before peak" if idx < max_idx else "Peak" if idx == max_idx else "After peak"
                                
                                if SEND_ANNOTATED_IMAGES:
                                    annotated_save_path = os.path.join(save_folder, f"mounting_detected_{ts}_conf{conf:.2f}_annotated.jpg")
                                    
                                    if img is not None:
                                        cv2.imwrite(annotated_save_path, img)
                                        send_path = annotated_save_path
                                    elif results_obj is not None:
                                        orig_frame = cv2.imread(original_path)
                                        if orig_frame is not None:
                                            annotated_frame = results_obj.plot()
                                            cv2.imwrite(annotated_save_path, annotated_frame)
                                            send_path = annotated_save_path
                                        else:
                                            logger.info(f"Could not load original frame for {original_path}, sending original")
                                            send_path = original_path
                                    else:
                                        logger.info(f"No result object available for {ts}, sending original")
                                        send_path = original_path
                                else:
                                    send_path = original_path
                                
                                sound_indicator = "🔊" if play_sound else "🔇"
                                message = f"{sound_indicator} Mounting detected - {CAMERA_NAME}\n"
                                message += f"Time: {ts}\n"
                                message += f"Confidence: {conf:.2f}\n"
                                message += f"Stage: {stage} - Rank {rank+1}/{len(selected_indices)}\n"
                                message += f"Event duration: {collection_duration:.1f}s\n"
                                
                                send_telegram_photo(send_path, message, disable_notification=not play_sound)
                                
                                sound_status = "WITH sound" if play_sound else "without sound"
                                logger.info(f"Telegram queued for {stage}: {conf:.2f} - {sound_status}")
                            
                            last_detection_time = current_time
                            logger.info(f"Cooldown period of {cooldown_period} seconds started")
                            
                            # Cleanup old detections after sending notification
                            cleanup_old_detections()
                            
                            if play_sound:
                                logger.info(f"🔊 SOUND NOTIFICATION #{notification_counter} queued!")
                            else:
                                logger.info(f"🔇 Silent notification #{notification_counter} queued (sound every {SOUND_EVERY_N_NOTIFICATIONS})")
                        else:
                            if max_conf < NOTIFY_THRESHOLD:
                                logger.info(f"Highest confidence ({max_conf:.2f}) lower than NOTIFY_THRESHOLD ({NOTIFY_THRESHOLD}). No notification sent.")
                            elif high_conf_detections < MIN_HIGH_CONFIDENCE_DETECTIONS:
                                logger.info(f"Too few high confidence detections ({high_conf_detections}/{MIN_HIGH_CONFIDENCE_DETECTIONS}). No notification sent.")
                    
                    collecting_screenshots = False
                    peak_detected = False
                    inactivity_period = 0
                    
                    if inactivity_period >= INACTIVITY_STOP_TIME:
                        logger.info(f"Collection stopped due to inactivity ({inactivity_period:.1f}s without detections)")
                    elif highest_conf >= 0.85 and collection_duration >= 1:
                        logger.info(f"Collection stopped due to very high confidence detection ({highest_conf:.2f})")
                    elif peak_detected and collection_duration >= MIN_COLLECTION_TIME:
                        logger.info(f"Collection stopped after peak detection and minimum collection time ({collection_duration:.1f}s)")
                    else:
                        logger.info(f"Collection stopped after maximum collection time ({collection_duration:.1f}s)")
            
            if SHOW_LIVE_FEED and len(results) > 0:
                annotated_frame = results[0].plot()
                cv2.imshow("Cowcatcher Detection", annotated_frame)
        
        if SHOW_LIVE_FEED and (cv2.waitKey(1) & 0xFF == ord('q')):
            logger.info("User pressed 'q'. Script will stop.")
            break

except KeyboardInterrupt:
    logger.info("Script stopped by user (Ctrl+C)")
    stop_reason = "Script manually stopped by user (Ctrl+C)"
except Exception as e:
    logger.info(f"Unexpected error: {str(e)}")
    stop_reason = f"Script stopped due to error: {str(e)}"
    
finally:
    logger.info(f"Waiting for {telegram_queue.qsize()} remaining Telegram tasks...")
    telegram_queue.join()
    
    telegram_queue.put(None)
    telegram_thread.join(timeout=10)
    
    cap.release()
    if SHOW_LIVE_FEED:
        cv2.destroyAllWindows()
    logger.info("Camera stream closed and resources released")
    logger.info(f"Total frames processed: {frame_count}")
    
    stop_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if 'stop_reason' not in locals():
        stop_reason = "Script stopped (reason unknown)"
    
    stop_message = f"⚠️ WARNING: Cowcatcher detection script stopped at {stop_time}\n"
    stop_message += f"Reason: {stop_reason}\n"
    stop_message += f"Total frames processed: {frame_count}\n"
    stop_message += f"Notifications sent: {telegram_stats['sent']}\n"
    stop_message += f"Failed: {telegram_stats['failed']}"
    
    _send_telegram_message_sync(stop_message)
    logger.info("Stop message sent to Telegram")
