"""
CowCatcher Script with Threading Optimization and Multi-Chat Support
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
import time
import requests
import json
from datetime import datetime
from collections import deque
from threading import Thread
from queue import Queue

# Config laden
with open('config.json') as f:
    config = json.load(f)

# Camera settings
CAMERA_ID = "camera1"  # verander dit per script
camera = next(c for c in config["cameras"] if c["id"] == CAMERA_ID)

#individual camera settings
CAMERA_NAME = camera["name"]
RTSP_URL = camera["rtsp_url"]
SHOW_LIVE_FEED = camera["show_live_feed"]
NOTIFY_THRESHOLD = camera["notify_threshold"]
PEAK_DETECTION_THRESHOLD = camera["peak_detection_threshold"]

#global settings
model_path = config['global_settings']['model_path']
SOUND_EVERY_N_NOTIFICATIONS = config["global_settings"]["sound_every_n_notifications"]
SAVE_THRESHOLD = config["global_settings"]["save_threshold"]
process_every_n_frames = config["global_settings"]["process_every_n_frames"]
MIN_HIGH_CONFIDENCE_DETECTIONS = config["global_settings"]["min_high_confidence_detections"]
MAX_SCREENSHOTS = config["global_settings"]["max_screenshots"]
SEND_ANNOTATED_IMAGES = config["global_settings"]["send_annotated_images"]
COLLECTION_TIME = config["global_settings"]["collection_time"]
MIN_COLLECTION_TIME = config["global_settings"]["min_collection_time"]
INACTIVITY_STOP_TIME = config["global_settings"]["inactivity_stop_time"]
cooldown_period = config["global_settings"]["cooldown_period"]

# Telegram settings - PER CAMERA
BOT_NAME = camera["telegram_bot"]  # Bot naam uit camera settings
telegram_bots = config["telegram"]["bots"]
TELEGRAM_BOT_TOKEN = next(b["token"] for b in telegram_bots if b["name"] == BOT_NAME and b["enabled"])

telegram_users = config["telegram"]["users"]
TELEGRAM_CHAT_IDS = [u["chat_id"] for u in telegram_users if u["enabled"]]

print("Starting CowCatcherAI. Loading detection model...")
model = YOLO(model_path, task='detect')
print("Detection model successfully loaded")

print(f"Connecting to camera: {CAMERA_NAME}")

#Folder for saving screenshots
save_folder = f"mounting_detections_{CAMERA_ID}"
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Folder '{save_folder}' created")
else:
    print(f"Folder '{save_folder}' already exists")

print(f"Telegram bot '{BOT_NAME}' configured for {len(TELEGRAM_CHAT_IDS)} chat(s)")

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
            print(f"ERROR in telegram worker: {str(e)}")

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
                print(f"ERROR sending Telegram photo to chat {chat_id}: {response.text}")
            else:
                success_count += 1
                
        except Exception as e:
            print(f"ERROR sending Telegram photo to chat {chat_id}: {str(e)}")
    
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
                print(f"ERROR sending Telegram message to chat {chat_id}: {response.text}")
            else:
                success_count += 1
                
        except Exception as e:
            print(f"ERROR sending Telegram message to chat {chat_id}: {str(e)}")
    
    return success_count > 0

def send_telegram_photo(image_path, caption, disable_notification=False):
    """Queue photo for sending (returns immediately)"""
    telegram_queue.put(('photo', image_path, caption, disable_notification))
    return True

def send_telegram_message(message):
    """Queue message for sending (returns immediately)"""
    telegram_queue.put(('message', message))
    return True
# END THREADING SETUP

def test_telegram_connection():
    """Test Telegram connection at startup - tests all chat IDs"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Telegram bot connection successfully tested.")
            
            # Test each chat ID
            valid_chats = []
            for chat_id in TELEGRAM_CHAT_IDS:
                try:
                    test_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChat"
                    test_response = requests.get(test_url, params={'chat_id': chat_id}, timeout=10)
                    if test_response.status_code == 200:
                        valid_chats.append(chat_id)
                        print(f"  ✓ Chat ID {chat_id} is valid")
                    else:
                        print(f"  ✗ Chat ID {chat_id} is invalid: {test_response.text}")
                except Exception as e:
                    print(f"  ✗ Could not verify chat ID {chat_id}: {str(e)}")
            
            if len(valid_chats) == 0:
                print("ERROR: No valid chat IDs found!")
                return False
            
            print(f"Successfully configured {len(valid_chats)}/{len(TELEGRAM_CHAT_IDS)} chat(s)")
            return True
        else:
            print(f"ERROR testing Telegram connection: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR testing Telegram connection: {str(e)}")
        return False

# Test Telegram connection
if not test_telegram_connection():
    print("Telegram connection failed, script will exit.")
    exit()

# Start Telegram worker thread
telegram_thread = Thread(target=telegram_worker, daemon=True)
telegram_thread.start()
print("Telegram worker thread started (async mode enabled)")

# Open the camera stream
print("Opening camera stream...")
cap = cv2.VideoCapture(RTSP_URL)
if not cap.isOpened():
    print("ERROR: Cannot open camera stream")
    exit()
else:
    print("Camera stream successfully opened")

frame_count = 0
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

print(f"Processing started, every {process_every_n_frames} frames will be analyzed")
print(f"Image save threshold: {SAVE_THRESHOLD}")
print(f"Notification send threshold: {NOTIFY_THRESHOLD}")
print(f"Peak detection threshold: {PEAK_DETECTION_THRESHOLD}")
print(f"Maximum {MAX_SCREENSHOTS} screenshots per event")
print(f"Collection time: {MIN_COLLECTION_TIME}-{COLLECTION_TIME} seconds")
print(f"Stops automatically after {INACTIVITY_STOP_TIME} seconds of inactivity")
print(f"Minimum {MIN_HIGH_CONFIDENCE_DETECTIONS} detections above {NOTIFY_THRESHOLD} required for notification")
print(f"Telegram images: {'With bounding boxes' if SEND_ANNOTATED_IMAGES else 'Without bounding boxes'}")
print(f"Sound notification every {SOUND_EVERY_N_NOTIFICATIONS} alerts")

start_message = f"📋 Cowcatcher detection script started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n⚠️ DISCLAIMER: Use at your own risk. This program uses Ultralytics YOLO and is subject to the GNU Affero General Public License v3.0 (AGPL-3.0)."
send_telegram_message(start_message)

def format_timestamp_for_display(ts):
    """Converteer YYYYMMDD naar DD-MM-YYYY formaat voor weergave"""
    return f"{ts[6:8]}-{ts[4:6]}-{ts[:4]}"

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
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Cannot read frame from camera")
            cap.release()
            time.sleep(5)
            cap = cv2.VideoCapture(RTSP_URL)
            continue
            
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Frames processed: {frame_count} | Queue: {telegram_queue.qsize()} | Sent: {telegram_stats['sent']} | Failed: {telegram_stats['failed']}")
        
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
                print(f"Starting screenshot collection for {COLLECTION_TIME} seconds (searching for peak moment)")
                collecting_screenshots = True
                collection_start_time = current_time
                event_detections = []
                peak_detected = False
                
                for i in range(len(confidence_history)):
                    if confidence_history[i] >= SAVE_THRESHOLD:
                        hist_frame = frame_history[i]
                        hist_timestamp = timestamp_history[i]
                        hist_conf = confidence_history[i]
                        
                        hist_original_save_path = os.path.join(save_folder, f"mounting_detected_{hist_timestamp}_conf{hist_conf:.2f}_history.jpg")
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
                    
                    print(f"Detection added to collection: {highest_conf:.2f}")
                    
                    inactivity_period = 0
                    last_detection_time = current_time
                    
                    if highest_conf >= PEAK_DETECTION_THRESHOLD and not peak_detected:
                        peak_detected = True
                        print(f"Possible peak detected with confidence {highest_conf:.2f}")
                else:
                    if last_detection_time is not None:
                        inactivity_period = (current_time - last_detection_time).total_seconds()
                        if inactivity_period >= 2:
                            print(f"Inactivity period: {inactivity_period:.1f}s")
                
                collection_duration = (current_time - collection_start_time).total_seconds()
                
                if (peak_detected and collection_duration >= MIN_COLLECTION_TIME) or \
                   collection_duration >= COLLECTION_TIME or \
                   (highest_conf >= 0.85 and collection_duration >= 1) or \
                   inactivity_period >= INACTIVITY_STOP_TIME:
                    
                    print(f"Collection stopped after {collection_duration:.1f} seconds with {len(event_detections)} detections")
                    
                    current_confidences = [conf for conf, _, _, _, _ in event_detections]
                    high_conf_detections = sum(1 for conf in current_confidences if conf >= NOTIFY_THRESHOLD)
                    print(f"Number of high confidence detections: {high_conf_detections}/{MIN_HIGH_CONFIDENCE_DETECTIONS} required")
                    
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
                                            print(f"Could not load original frame for {original_path}, sending original")
                                            send_path = original_path
                                    else:
                                        print(f"No result object available for {ts}, sending original")
                                        send_path = original_path
                                else:
                                    send_path = original_path
                                
                                sound_indicator = "🔊" if play_sound else "🔇"
                                date_str = format_timestamp_for_display(ts)
                                conf_str = f"{conf:.2f}".replace('.', ',')

                                message = f"{sound_indicator} Mounting detected {date_str} - confidence: {conf_str}\n"
                                message += f"Stage: {stage} - Rank {rank+1}/{len(selected_indices)}\n"
                                                                
                                send_telegram_photo(send_path, message, disable_notification=not play_sound)
                                
                                sound_status = "WITH sound" if play_sound else "without sound"
                                print(f"Telegram queued for {stage}: {conf:.2f} - {sound_status}")
                            
                            last_detection_time = current_time
                            print(f"Cooldown period of {cooldown_period} seconds started")
                            
                            if play_sound:
                                print(f"🔊 SOUND NOTIFICATION #{notification_counter} queued!")
                            else:
                                print(f"🔇 Silent notification #{notification_counter} queued (sound every {SOUND_EVERY_N_NOTIFICATIONS})")
                        else:
                            if max_conf < NOTIFY_THRESHOLD:
                                print(f"Highest confidence ({max_conf:.2f}) lower than NOTIFY_THRESHOLD ({NOTIFY_THRESHOLD}). No notification sent.")
                            elif high_conf_detections < MIN_HIGH_CONFIDENCE_DETECTIONS:
                                print(f"Too few high confidence detections ({high_conf_detections}/{MIN_HIGH_CONFIDENCE_DETECTIONS}). No notification sent.")
                    
                    collecting_screenshots = False
                    peak_detected = False
                    inactivity_period = 0
                    
                    if inactivity_period >= INACTIVITY_STOP_TIME:
                        print(f"Collection stopped due to inactivity ({inactivity_period:.1f}s without detections)")
                    elif highest_conf >= 0.85 and collection_duration >= 1:
                        print(f"Collection stopped due to very high confidence detection ({highest_conf:.2f})")
                    elif peak_detected and collection_duration >= MIN_COLLECTION_TIME:
                        print(f"Collection stopped after peak detection and minimum collection time ({collection_duration:.1f}s)")
                    else:
                        print(f"Collection stopped after maximum collection time ({collection_duration:.1f}s)")
            
            if SHOW_LIVE_FEED and len(results) > 0:
                annotated_frame = results[0].plot()
                cv2.imshow("Cowcatcher Detection", annotated_frame)
        
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
    print(f"Waiting for {telegram_queue.qsize()} remaining Telegram tasks...")
    telegram_queue.join()
    
    telegram_queue.put(None)
    telegram_thread.join(timeout=10)
    
    cap.release()
    if SHOW_LIVE_FEED:
        cv2.destroyAllWindows()
    print("Camera stream closed and resources released")
    print(f"Total frames processed: {frame_count}")
    
    stop_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if 'stop_reason' not in locals():
        stop_reason = "Script stopped (reason unknown)"
    
    stop_message = f"⚠️ WARNING: Cowcatcher detection script stopped at {stop_time}\n"
    stop_message += f"Reason: {stop_reason}\n"
    stop_message += f"Failed: {telegram_stats['failed']}"
    
    _send_telegram_message_sync(stop_message)
    print("Stop message sent to Telegram")

