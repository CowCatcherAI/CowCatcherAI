"""
CowCatcher AI Web Configuration Interface
Provides a simple web UI for configuring the CowCatcher detection system
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, Response
from functools import wraps
import os
import json
import glob
import psutil
import cv2
import threading
import time
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Authentication credentials from environment variables
WEBUI_USERNAME = os.environ.get('WEBUI_USERNAME', 'admin')
WEBUI_PASSWORD = os.environ.get('WEBUI_PASSWORD', 'admin')
USE_DEFAULT_CREDENTIALS = (
    os.environ.get('WEBUI_USERNAME') is None or 
    os.environ.get('WEBUI_PASSWORD') is None
)

# Use Docker path if running in container, otherwise use local path
DATA_DIR = '/app/data' if os.path.exists('/app') else './data'
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
MODEL_DIR = '/app' if os.path.exists('/app') else '.'
DETECTIONS_DIR = os.path.join(DATA_DIR, 'mounting_detections')
LOG_FILE = os.path.join(DATA_DIR, 'cowcatcher.log')
ALLOWED_EXTENSIONS = {'pt'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

def ensure_dirs():
    """Ensure required directories exist"""
    Path(CONFIG_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(DETECTIONS_DIR).mkdir(parents=True, exist_ok=True)

def load_config():
    """Load configuration from file or return defaults"""
    ensure_dirs()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Backward compatibility: rename rtsp_url_camera1 to rtsp_url
                if 'rtsp_url_camera1' in config and 'rtsp_url' not in config:
                    config['rtsp_url'] = config['rtsp_url_camera1']
                    del config['rtsp_url_camera1']
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    ensure_dirs()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_system_stats():
    """Get system CPU and memory usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(DATA_DIR)
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_total_gb': disk.total / (1024**3)
        }
    except Exception as e:
        print(f"Error getting system stats: {e}")
        return None

def get_detections(limit=500):
    """Get list of detection images"""
    try:
        if not os.path.exists(DETECTIONS_DIR):
            return []
        
        # Get all jpg files
        files = glob.glob(os.path.join(DETECTIONS_DIR, '*.jpg'))
        
        # Sort by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        
        # Limit results
        files = files[:limit]
        
        # Extract metadata
        detections = []
        for filepath in files:
            filename = os.path.basename(filepath)
            stat = os.stat(filepath)
            detections.append({
                'filename': filename,
                'timestamp': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'size': stat.st_size
            })
        
        return detections
    except Exception as e:
        print(f"Error getting detections: {e}")
        return []

def cleanup_old_detections(max_keep):
    """Remove old detection files beyond the limit"""
    try:
        if not os.path.exists(DETECTIONS_DIR):
            return 0
        
        files = glob.glob(os.path.join(DETECTIONS_DIR, '*.jpg'))
        files.sort(key=os.path.getmtime, reverse=True)
        
        removed = 0
        for filepath in files[max_keep:]:
            try:
                os.remove(filepath)
                removed += 1
            except Exception as e:
                print(f"Error removing {filepath}: {e}")
        
        return removed
    except Exception as e:
        print(f"Error cleaning up detections: {e}")
        return 0

def get_log_tail(lines=500):
    """Get the last N lines of the log file"""
    try:
        if not os.path.exists(LOG_FILE):
            return "Log file not found. The detection script may not be running yet."
        
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception as e:
        return f"Error reading log: {str(e)}"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == WEBUI_USERNAME and password == WEBUI_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error=True, use_default=USE_DEFAULT_CREDENTIALS)
    
    return render_template('login.html', error=False, use_default=USE_DEFAULT_CREDENTIALS)

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Main menu page"""
    return render_template('index.html')

@app.route('/settings')
@login_required
def settings():
    """Settings configuration page"""
    config = load_config()
    return render_template('settings.html', config=config)

@app.route('/detections')
@login_required
def detections():
    """Detections list page"""
    config = load_config()
    max_keep = config.get('max_detections_to_keep', 500)
    detections_list = get_detections(max_keep)
    return render_template('detections.html', detections=detections_list, count=len(detections_list))

@app.route('/statistics')
@login_required
def statistics():
    """Statistics page"""
    stats = get_system_stats()
    return render_template('statistics.html', stats=stats)

@app.route('/logs')
@login_required
def logs():
    """Logs viewer page"""
    log_content = get_log_tail(500)
    return render_template('logs.html', log_content=log_content)

@app.route('/live')
@login_required
def live():
    """Live camera feed page"""
    config = load_config()
    return render_template('live.html', config=config)

@app.route('/save', methods=['POST'])
@login_required
def save():
    """Save configuration from form"""
    try:
        config = {
            'rtsp_url': request.form.get('rtsp_url', ''),
            'camera_name': request.form.get('camera_name', 'Camera 1'),
            'model_path': request.form.get('model_path', 'CowcatcherV14.pt'),
            'telegram_bot_token': request.form.get('telegram_bot_token', ''),
            'telegram_chat_ids': request.form.get('telegram_chat_ids', ''),
            'save_threshold': float(request.form.get('save_threshold', 0.75)),
            'notify_threshold': float(request.form.get('notify_threshold', 0.86)),
            'peak_detection_threshold': float(request.form.get('peak_detection_threshold', 0.89)),
            'max_screenshots': int(request.form.get('max_screenshots', 2)),
            'collection_time': int(request.form.get('collection_time', 50)),
            'min_collection_time': int(request.form.get('min_collection_time', 4)),
            'inactivity_stop_time': int(request.form.get('inactivity_stop_time', 6)),
            'min_high_confidence_detections': int(request.form.get('min_high_confidence_detections', 3)),
            'cooldown_period': int(request.form.get('cooldown_period', 40)),
            'sound_every_n_notifications': int(request.form.get('sound_every_n_notifications', 5)),
            'max_detections_to_keep': int(request.form.get('max_detections_to_keep', 500)),
            'show_live_feed': request.form.get('show_live_feed') == 'on',
            'send_annotated_images': request.form.get('send_annotated_images') == 'on',
            'developer_mode': request.form.get('developer_mode') == 'on',
            'use_video_file': request.form.get('use_video_file') == 'on',
            'video_file_path': request.form.get('video_file_path', '')
        }
        
        if save_config(config):
            # Cleanup old detections if needed
            max_keep = config.get('max_detections_to_keep', 500)
            cleanup_old_detections(max_keep)
            return redirect(url_for('settings'))
        else:
            return "Error saving configuration", 500
    except Exception as e:
        return f"Error: {str(e)}", 400

@app.route('/upload_model', methods=['POST'])
@login_required
def upload_model():
    """Upload AI model file"""
    try:
        if 'model_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['model_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only .pt files are allowed'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(MODEL_DIR, filename)
        file.save(filepath)
        
        # Update config with new model path
        config = load_config()
        config['model_path'] = filename
        save_config(config)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload_video', methods=['POST'])
@login_required
def upload_video():
    """Upload video file for developer mode"""
    try:
        if 'video_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['video_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file extension
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in VIDEO_EXTENSIONS):
            return jsonify({'success': False, 'error': 'Only video files are allowed (mp4, avi, mov, mkv)'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(DATA_DIR, filename)
        file.save(filepath)
        
        # Update config with new video path
        config = load_config()
        config['video_file_path'] = filepath
        save_config(config)
        
        return jsonify({'success': True, 'filename': filename, 'path': filepath})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/detection_image/<filename>')
@login_required
def detection_image(filename):
    """Serve detection images"""
    return send_from_directory(DETECTIONS_DIR, filename)

@app.route('/api/config', methods=['GET'])
@login_required
def get_config():
    """API endpoint to get current configuration"""
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
@login_required
def update_config():
    """API endpoint to update configuration"""
    try:
        config = request.json
        if save_config(config):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save configuration'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for system statistics"""
    stats = get_system_stats()
    if stats:
        return jsonify(stats)
    else:
        return jsonify({'error': 'Failed to get system stats'}), 500

@app.route('/api/detections')
@login_required
def api_detections():
    """API endpoint for detections list"""
    config = load_config()
    max_keep = config.get('max_detections_to_keep', 500)
    return jsonify(get_detections(max_keep))

@app.route('/api/logs')
@login_required
def api_logs():
    """API endpoint for log content"""
    return jsonify({'log': get_log_tail(500)})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

@app.route('/api/status')
def api_status():
    """API endpoint for component status"""
    status_file = os.path.join(DATA_DIR, 'status.json')
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status_data = json.load(f)
        else:
            status_data = {}
        
        # Add web UI status
        status_data['webui'] = {
            'status': 'ok',
            'message': 'Web interface running',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status_data)
    except Exception as e:
        return jsonify({'error': f'Could not read status: {str(e)}'}), 500

# Global variables for video streaming
camera_stream = None
stream_lock = threading.Lock()

class CameraStream:
    """Thread-safe camera stream handler"""
    def __init__(self, source):
        self.source = source
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.last_access = time.time()
        
    def start(self):
        """Start the camera stream"""
        if self.running:
            return
            
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise Exception(f"Could not open camera stream: {self.source}")
            
        # Set buffer size to reduce latency
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.running = True
        self.thread = threading.Thread(target=self._update_frame)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the camera stream"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            
    def _update_frame(self):
        """Update frame in background thread"""
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                # Resize frame to reduce bandwidth
                height, width = frame.shape[:2]
                if width > 640:
                    scale = 640 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                self.frame = frame
                self.last_access = time.time()
            else:
                time.sleep(0.1)
                
    def get_frame(self):
        """Get the current frame"""
        self.last_access = time.time()
        return self.frame
        
    def is_stale(self, timeout=30):
        """Check if stream hasn't been accessed recently"""
        return time.time() - self.last_access > timeout

def generate_frames():
    """Generate frames for MJPEG streaming"""
    global camera_stream
    config = load_config()
    
    # Determine video source
    if config.get('developer_mode') and config.get('use_video_file'):
        source = config.get('video_file_path', '')
        if not os.path.exists(source):
            source = os.path.join(DATA_DIR, '13665569_2160_2160_30fps.mp4')
    else:
        source = config.get('rtsp_url', '')
    
    if not source:
        # Generate error frame
        error_frame = generate_error_frame("No video source configured")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
        return
    
    try:
        with stream_lock:
            if camera_stream is None or camera_stream.source != source:
                if camera_stream:
                    camera_stream.stop()
                camera_stream = CameraStream(source)
                camera_stream.start()
        
        while True:
            frame = camera_stream.get_frame()
            if frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)  # Control frame rate
            
    except Exception as e:
        # Generate error frame
        error_frame = generate_error_frame(f"Stream error: {str(e)}")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')

def generate_error_frame(message):
    """Generate an error frame with a message"""
    import numpy as np
    
    # Create a black image
    img = np.zeros((240, 640, 3), dtype=np.uint8)
    
    # Add error message
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    color = (0, 0, 255)  # Red
    thickness = 2
    
    # Calculate text size and position
    text_size = cv2.getTextSize(message, font, font_scale, thickness)[0]
    text_x = (img.shape[1] - text_size[0]) // 2
    text_y = (img.shape[0] + text_size[1]) // 2
    
    cv2.putText(img, message, (text_x, text_y), font, font_scale, color, thickness)
    
    # Encode as JPEG
    ret, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buffer.tobytes()

@app.route('/video_feed')
@login_required
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream_status')
@login_required
def stream_status():
    """Check if video stream is available"""
    config = load_config()
    
    # Determine video source
    if config.get('developer_mode') and config.get('use_video_file'):
        source = config.get('video_file_path', '')
        source_type = "video_file"
        if not os.path.exists(source):
            source = os.path.join(DATA_DIR, '13665569_2160_2160_30fps.mp4')
    else:
        source = config.get('rtsp_url', '')
        source_type = "rtsp"
    
    available = bool(source)
    if source_type == "video_file":
        available = available and os.path.exists(source)
    
    return jsonify({
        'available': available,
        'source': source,
        'source_type': source_type
    })

# Cleanup stale streams periodically
def cleanup_streams():
    """Cleanup stale camera streams"""
    global camera_stream
    while True:
        time.sleep(60)  # Check every minute
        with stream_lock:
            if camera_stream and camera_stream.is_stale():
                camera_stream.stop()
                camera_stream = None

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_streams, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
