# CowCatcher AI 🐄📱

An automatic "Heat detection system" that monitors cows 24/7 and sends direct notifications via Telegram (messaging app) when "mounting"behavior is detected.

## 📋 Overview

CowCatcher AI is an open-source system that uses artificial intelligence to automatically recognize when a cow displays estrus behavior (mounting other cows). The system analyzes live camera footage and sends direct photos with notifications to your phone via Telegram.

![readme file afbeelding](https://github.com/user-attachments/assets/cee1e5f5-f9ae-4241-b8ad-8a9313b4a70c)

📷 barn camera footage ──→ 🤖 AI Computer Vision ──→ ⚡ *mounting* detection ──→ 💽 save image ──→ 📲 Telegram notification with image

### Key Features
- **24/7 monitoring** of live camera footage
- **Automatic detection** of in heat behavior with AI
- **Direct notifications** via Telegram with photos
- **Local and secure** – your data stays on your farm
- **Open source** - fully customizable and transparent
- **completely free software** one-time setup and lifetime usage
- **affordable and scalable** for 1 calf pen or complete barn
- **Easy deployment** with Docker - no complex installation needed
- **Web UI** for easy configuration

## 🛠️ Requirements

### Bare minimum (for getting started)
- **Docker** and Docker Compose installed
- **any IP camera** with RTSP support
- **Internet connection**
- **AI Model file** (CowcatcherV14.pt or similar)

### Hardware (for best performance)
- **Computer** with NVIDIA graphics card (€600-1000 for 1-4 cameras)
- **any IP camera** with RTSP support (€80-170)
- **PoE switch** for cameras (€80 for 4 ports)
- **LAN cables** (€1 per meter)
- **Internet connection**
- **Scalable** more cameras require more powerful computer

## 🐳 Quick Start with Docker (Recommended)

### Prerequisites
1. Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
2. Download or clone this repository: `git clone https://github.com/sjoerdvanderhoorn/CowCatcherAI.git`

### Step 1: Start the Container

```bash
# Navigate to the project directory
cd CowCatcherAI

# Start the container
docker-compose up -d
```

### Step 2: Configure via Web UI

1. Open your browser and navigate to `http://localhost:5000`
2. **Login** with default credentials: username `admin`, password `admin`
   - ⚠️ **Security Note**: For production use, set custom credentials via environment variables `WEBUI_USERNAME` and `WEBUI_PASSWORD` in `docker-compose.yml`
3. Navigate to Settings
4. Upload your AI model file (e.g., `CowcatcherV14.pt`)
   - The model file is required for the detection system to work
   - Contact the project maintainer if you need access to the model file
4. Fill in your configuration:
   - **Camera RTSP URL** (e.g., `rtsp://admin:password@192.168.1.100:554/h264Preview_01_sub`)
   - **Telegram Bot Token** (get from @BotFather on Telegram)
   - **Telegram Chat IDs** (get from @userinfobot, comma-separated)
   - Adjust detection thresholds as needed
5. Click **Save Configuration**

Configuration changes take effect automatically - no restart needed!

### Step 3: Monitor Logs

```bash
# View live logs
docker-compose logs -f cowcatcher

# Stop the container
docker-compose down
```

### Data Persistence

All configuration and detection images are stored in the `./data` directory on your host machine, which persists across container restarts.

## 🤖 Setting Up Telegram Bot

### Step 1: Create Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Give your bot a name: "e.g.:" `Estrus Detection`
4. Give your bot a username: `EstrusDetectionBot`
5. **Save the API token** you receive, NEVER share this token

### Step 2: Get Your User ID
1. Search for `@userinfobot` in Telegram
2. Start a chat and send `/start`
3. **Note your personal Telegram ID**

### Step 3: Configure in Web UI
Use the web interface at `http://localhost:5000` to enter your Telegram credentials.

## 🧑‍💻 Development with Docker

For development, you can use Docker with volume mounts to allow live code editing:

### Prerequisites
- Docker and Docker Compose installed
- Code editor of your choice

### Setup

```bash
# Clone the repository
git clone https://github.com/sjoerdvanderhoorn/CowCatcherAI.git
cd CowCatcherAI

# The docker-compose.yml already mounts ./data for persistence
# For development, you can modify files directly in the repository
# and rebuild the container to test changes

# Build and start
docker-compose up --build

# To rebuild after code changes
docker-compose up --build -d

# View logs
docker-compose logs -f
```

### Making Code Changes

1. Edit files in the repository
2. Rebuild the container: `docker-compose up --build -d`
3. Test your changes via the web UI or logs

### Running Without Docker (Advanced)

For local development without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p data

# Run the web UI
python webui.py

# In another terminal, run the detection system
python cowcatcher_docker.py
```

## 📁 Project Structure

```
CowCatcherAI/
├── README.md
├── LICENSE
├── Dockerfile                    # Docker container definition
├── docker-compose.yml            # Docker Compose configuration
├── requirements.txt              # Python dependencies
├── startup.sh                    # Container startup script
├── cowcatcher/                   # Detection system
│   ├── cowcatcher.py            # Main detection script
│   └── config_loader.py         # Configuration loader
├── webui/                        # Web interface
│   ├── webui.py                 # Web UI application
│   └── templates/               # Web UI templates
│       ├── index.html           # Main menu page
│       ├── login.html           # Login page
│       ├── settings.html        # Settings page
│       ├── detections.html      # Detections history page
│       ├── live.html            # Live feed page
│       ├── statistics.html      # System statistics page
│       └── logs.html            # Log viewer page
└── data/                         # Persistent data (config & detections)
    ├── config.json              # Configuration file
    ├── cowcatcher.log           # Application logs
    └── mounting_detections/     # Saved detection images
```

## ⚙️ Configuration Options

All configuration is done through the web UI at `http://localhost:5000`. Available settings include:

### Camera Settings
- **Camera Name**: Friendly name shown in Telegram notifications
- **RTSP URL**: Camera stream address
- **Model Upload**: Upload AI model file directly via web UI
- **Model Path**: AI model filename
- **Developer Mode**: Enable testing with video files instead of live camera

### Telegram Settings
- **Bot Token**: Telegram bot API token
- **Chat IDs**: Comma-separated list of recipient chat IDs

### Detection Thresholds
- **Save Threshold** (0.5-1.0): Minimum confidence to save images (default: 0.75)
- **Notification Threshold** (0.5-1.0): Minimum confidence to send notifications (default: 0.86)
- **Peak Detection Threshold** (0.5-1.0): Threshold for peak detection (default: 0.89)
- **Min High Confidence Detections**: Required detections above notify threshold (default: 3)

### Collection Settings
- **Maximum Collection Time**: Maximum time to collect screenshots (default: 50s)
- **Minimum Collection Time**: Minimum time to collect (default: 4s)
- **Inactivity Stop Time**: Stop collection after inactivity (default: 6s)
- **Cooldown Period**: Time between consecutive notifications (default: 40s)

### Notification Settings
- **Max Screenshots**: Number of photos per notification (default: 2)
- **Sound Every N Notifications**: Play sound every N notifications (default: 5)
- **Max Detections to Keep**: Maximum number of detection images to store (default: 500)
- **Send Annotated Images**: Send images with bounding boxes (default: Yes)
- **Show Live Feed**: Show live feed display (requires display, default: No)

## 📄 License

This project uses the GNU Affero General Public License v3.0 (AGPL-3.0). It is based on Ultralytics YOLO and is fully open source.
IMPORTANT NOTICE: This software/model is NOT authorized for commercial use or distribution.

## 🐳 Docker Commands Reference

```bash
# Start the container in background
docker-compose up -d

# View logs
docker-compose logs -f

# Restart after configuration changes
docker-compose restart

# Stop the container
docker-compose stop

# Stop and remove container
docker-compose down

# Rebuild container after code changes
docker-compose up -d --build

# Check container status
docker-compose ps

# Access container shell for debugging
docker-compose exec cowcatcher /bin/bash
```

## 🔧 Troubleshooting

### Container won't start
- Check Docker logs: `docker-compose logs cowcatcher`
- Ensure port 5000 is not already in use
- Verify the AI model file exists in the project directory

### Can't connect to camera
- Verify RTSP URL is correct
- Test camera connection from host machine
- Check network connectivity between container and camera
- Ensure camera is on the same network or accessible

### Telegram notifications not working
- Verify bot token is correct
- Check chat IDs are valid
- Test bot with @BotFather
- Check internet connectivity from container

### Configuration not persisting
- Ensure `./data` directory exists and is writable
- Check volume mapping in docker-compose.yml
- Restart container after configuration changes

### Performance issues
- Monitor CPU/GPU usage: `docker stats cowcatcher-ai`
- Consider reducing detection frequency
- Check camera stream resolution
- For GPU support, use nvidia-docker runtime

## 🙏 Acknowledgments

This project is made possible by the amazing [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) library. Their state-of-the-art computer vision technology forms the foundation for our AI detection of estrus behavior in cows.

**Thank you Ultralytics team!** 🚀 For making cutting-edge AI technology available that now also helps Dutch farmers.

## 🤝 Contributing

This is an open source project. You may modify and improve it as you see fit. Contributions are welcome via pull requests.

## 📞 Support

For questions or support, please contact via the project repository or community channels, we have a page on facebook https://www.facebook.com/groups/1765616710830233 and Telegram https://t.me/+SphG4deaWVNkYTQ8
For direct contact with the main contributor/project creator: jacobsfarmsocial@gmail.com

---
⚠️ Disclaimer

Use at your own risk.
This software is intended as a tool and does not replace professional knowledge and experience. The AI may give false notifications; the user remains responsible for the final assessment and decision. Physical inspection and identification of the animal remain essential.

Although this solution is designed to be user-friendly and efficient, the underlying technology is not new. The computer vision used is based on YOLO, a proven technique that has been applied for years for object and motion detection. The Telegram notifications also use an existing API. Despite appearing innovative, it involves a smart combination of existing technologies.
