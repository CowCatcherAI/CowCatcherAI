"""
Configuration loader for CowCatcher AI
Loads settings from JSON config file or environment variables
"""
import os
import json
from pathlib import Path

# Use Docker path if running in container, otherwise use local path
DATA_DIR = '/app/data' if os.path.exists('/app') else './data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')

# Default configuration
DEFAULT_CONFIG = {
    'rtsp_url': 'rtsp://admin:password@192.168.1.100:554/h264Preview_01_sub',
    'camera_name': 'Camera 1',
    'model_path': 'CowcatcherV14.pt',
    'telegram_bot_token': '',
    'telegram_chat_ids': '',
    'save_threshold': 0.75,
    'notify_threshold': 0.86,
    'peak_detection_threshold': 0.89,
    'max_screenshots': 2,
    'collection_time': 50,
    'min_collection_time': 4,
    'inactivity_stop_time': 6,
    'min_high_confidence_detections': 3,
    'cooldown_period': 40,
    'sound_every_n_notifications': 5,
    'show_live_feed': False,
    'send_annotated_images': True,
    'max_detections_to_keep': 500,
    'developer_mode': False,
    'use_video_file': False,
    'video_file_path': ''
}

def load_config():
    """Load configuration from JSON file"""
    config = DEFAULT_CONFIG.copy()
    
    # Load from JSON file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return config

def get_config():
    """Get the current configuration"""
    config = load_config()
    
    # Backward compatibility: if rtsp_url_camera1 exists, rename it to rtsp_url
    if 'rtsp_url_camera1' in config and 'rtsp_url' not in config:
        config['rtsp_url'] = config['rtsp_url_camera1']
        del config['rtsp_url_camera1']
    
    # Parse telegram_chat_ids from comma-separated string to list
    if isinstance(config['telegram_chat_ids'], str):
        config['telegram_chat_ids'] = [
            cid.strip() 
            for cid in config['telegram_chat_ids'].split(',') 
            if cid.strip()
        ]
    
    return config

# Legacy support - expose as module-level variables for backward compatibility
config = get_config()
RTSP_URL = config.get('rtsp_url', config.get('rtsp_url_camera1', ''))
MODEL_PATH = config['model_path']
TELEGRAM_BOT_TOKEN = config['telegram_bot_token']
TELEGRAM_CHAT_IDS = config['telegram_chat_ids']
