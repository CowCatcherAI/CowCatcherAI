# CowCatcher AI 🐄📱

An automatic "Heat detection system" that monitors cows 24/7 and sends direct notifications via Telegram (messaging app) when "mounting" behavior is detected.

## 📋 Overview

CowCatcher AI is an open-source system that uses artificial intelligence to automatically recognize when a cow displays estrus behavior (mounting other cows). The system analyzes live camera footage and sends direct photos with notifications to your phone via Telegram.

![readme file afbeelding](https://github.com/user-attachments/assets/cee1e5f5-f9ae-4241-b8ad-8a9313b4a70c)

📷 barn camera footage ──→ 🤖 AI Computer Vision ──→ ⚡ mounting detection ──→ 💽 save image ──→ 📲 Telegram notification with image

### Key Features
- **Zero Setup**: No Python, Anaconda, or coding required. Just download and run.
- **24/7 monitoring** of live camera footage
- **Automatic detection** of in heat behavior with AI
- **Direct notifications** via Telegram with photos
- **Local and secure** – your data stays on your farm
- **Open source** - fully customizable and transparent
- **Free software** - one-time setup and lifetime usage

## 🛠️ Requirements

### Hardware
- **Computer with NVIDIA Graphics Card**: GTX 1600-series or newer (e.g., GTX 1660, RTX 3060, RTX 4060).
  - *Note: The executable requires a GTX 1600-series or newer. For older cards (e.g., GTX 10-series), please use the Docker version.*
- **IP Camera**: Any camera with RTSP support (€80-170).
- **Internet Connection**: For sending Telegram notifications.

### Software
- **CowCatcher AI Executable**: Download from the [AI Detector Releases](https://github.com/ESchouten/ai-detector/releases) page.
- **Telegram App**: To receive notifications.

## 🚀 Getting Started

### Step 1: Create Telegram Bot
1. Open Telegram and search for **@BotFather**.
2. Send `/newbot`.
3. Name it (e.g., `MyFarmBot`).
4. Give it a username (e.g., `MyFarmBot_123`).
5. **Save the API Token** (you will need this).

### Step 2: Get Your User ID
1. Search for **@userinfobot** in Telegram.
2. Send `/start`.
3. **Save your ID** (you will need this).

### Step 3: Download & Configure
1. Download the latest `aidetector.exe` from the [Releases Page](https://github.com/ESchouten/ai-detector/releases).
2. Create a file named `config.json` in the same folder with the following content:

```json
{
    "detectors": [
        {
            "model": "https://github.com/CowCatcherAI/CowCatcherAI/releases/download/modelv-14/cowcatcherV15.pt",
            "sources": [
                "rtsp://username:password@192.168.1.100:554/stream"
            ],
            "detection": {
                "confidence": 0.7,
                "time_max": 50,
                "timeout": 6,
                "frames_min": 3
            },
            "exporters": {
                "telegram": {
                    "token": "YOUR_BOT_TOKEN_HERE",
                    "chat": "YOUR_USER_ID_HERE",
                    "confidence": 0.84
                },
                "disk": {
                    "directory": "mounts"
                }
            }
        }
    ]
}
```

3. Replace `YOUR_BOT_TOKEN_HERE` and `YOUR_USER_ID_HERE` with your values from Steps 1 & 2.
4. Replace the `sources` URL with your camera's RTSP stream URL.

### Step 4: Run
Double-click `aidetector.exe`. It will automatically load `config.json` from the same folder. A terminal window will open showing the detection logs.

## 🐳 Docker Usage

For users who prefer Docker, we provide a pre-built image.

### Prerequisites
- Docker & Docker Compose
- **NVIDIA Container Toolkit** (required for GPU support)

### Run with Docker Compose
1. Create a `compose.yml` file:

```yaml
services:
  aidetector:
    image: "ghcr.io/eschouten/ai-detector:latest"

    volumes:
      - ./config.json:/app/config.json:ro

      - type: bind
        source: ./detections/
        target: /app/detections

    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
```

2. Ensure your `config.json` is in the same directory.
3. Run:
```bash
docker compose up -d
```

## 📄 License
This project uses the GNU Affero General Public License v3.0 (AGPL-3.0). It is based on Ultralytics YOLO and is fully open source. IMPORTANT NOTICE: This software/model is NOT authorized for commercial use or distribution.

## 🙏 Acknowledgments
This project is made possible by the amazing [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) library. Their state-of-the-art computer vision technology forms the foundation for our AI detection of estrus behavior in cows.

## 📞 Support
For questions or support, please contact via the project repository or community channels:
- Facebook: [CowCatcher AI Group](https://www.facebook.com/groups/1765616710830233)
- Telegram: [CowCatcher AI Chat](https://t.me/+SphG4deaWVNkYTQ8)
- Email: [cowcatcherai@gmail.com](mailto:cowcatcherai@gmail.com)

⚠️ **Disclaimer**: Use at your own risk. This software is intended as a tool and does not replace professional knowledge and experience. The AI may give false notifications; the user remains responsible for the final assessment and decision.
