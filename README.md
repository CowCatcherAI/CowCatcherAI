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

## 🛠️ Requirements

### Hardware (for best performance)
- **Computer** with NVIDIA graphics card (€600-1000 for 1-4 cameras)
- **IP camera** with RTSP support (€80-170)
- **PoE switch** for cameras (€80 for 4 ports)
- **LAN cables** (€1 per meter)
- **Internet connection**
- **Scalable** more cameras require more powerful computer

### Software
- Anaconda Python
- Sublime Text or Visual Studio Code (optional)
- WinRAR/7-Zip for extracting files

## 📥 Installation

### Step 1: Download Software
1. Download and install [Anaconda](https://www.anaconda.com/products/distribution)
2. Download and install [Sublime Text](https://www.sublimetext.com/) (optional)
3. Download and install [WinRAR](https://www.win-rar.com/) or 7-Zip
4. Download the latest release of [CowCatcherAI](https://github.com/CowCatcherAI/CowCatcherAI/releases)

### Step 2: Prepare Project
1. Extract the zip file to a folder of your choice (e.g., `C:\Users\username\Documents\Cowcatcherai`)
2. Remember the path to this folder, you'll need to reference it constantly

### Step 3: Set Up Python Environment

Open **Anaconda Prompt** and execute the following commands:

```bash
# Navigate to your project drive (replace C: with your drive)
C:

# Go to your project folder
cd \Users\username\Documents\Cowcatcherai

# Create a new conda environment
conda create -n cowcatcherai python=3.11

# Confirm with 'y' when prompted
y

# Activate the environment
conda activate cowcatcher
```

### Step 4: Install Required Packages

```bash
# Install Ultralytics YOLO
pip install ultralytics
```

### Step 5: Check GPU Support, for nvidia drivers

```bash
# Install PyTorch with CUDA support
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Start Python
python

# Test CUDA availability
import torch
torch.cuda.is_available()

# Should return 'True' for GPU support
# Exit Python
exit()
```

### Step 6: Configure Batch File (Optional)
Create or modify the provided batch file for easy startup. Update the variables according to your setup:

```batch
@echo off
REM Configuration - modify these variables as needed
REM To see version conda in anaconda prompt = echo %CONDA_PREFIX%
set CONDA_PATH="C:\ProgramData\anaconda3\Scripts\activate.bat"
set PROJECT_DRIVE=C:
set PROJECT_FOLDER=CowCatcherAI
set SCRIPT_NAME=cowcatcher.py

REM Execute the script
call %CONDA_PATH%
%PROJECT_DRIVE%
cd %PROJECT_FOLDER%
python %SCRIPT_NAME%
pause
```

**Customizable Variables:**
- `CONDA_PATH`: Path to your Anaconda installation
- `PROJECT_DRIVE`: Drive letter where your project is located
- `PROJECT_FOLDER`: Name of your project folder
- `SCRIPT_NAME`: Name of the main Python script

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

### Step 3: Set Up Configuration
Edit the `config.py` file in your project folder:

```python
# Telegram configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_ID_HERE"

# Camera configuration
RTSP_URL_CAMERA1 = "rtsp://username:password@IP_ADDRESS:554/stream"
```

## 🚀 Starting the System
Use the configured .bat file, or follow these steps:

```bash
# Navigate to your project folder
C:
cd CowCatcherAI

# Start the detection program
python cowcatcher.py
```

Upon successful startup, you'll receive a confirmation message in Telegram.

## ⚙️ Configuration Options

The system has various adjustable threshold values:

- **SAVE_THRESHOLD** (0.7): Threshold for saving images
- **NOTIFY_THRESHOLD** (0.85): Threshold for sending notifications
- **PEAK_DETECTION_THRESHOLD** (0.90): Threshold for peak detection
- **COOLDOWN_PERIOD** (40 seconds): Time between notifications
- **MAX_SCREENSHOTS** (2): Number of photos per notification
- **SOUND_EVERY_N_NOTIFICATIONS** Notification WITH sound every 5 messages

## 📁 Project Structure

```
CowCatcherAI/
├── README.md
├── LICENSE
├── CowcatcherVx.pt          # AI model file
├── Cowcatcher.py            # Main program
├── config.py                # Configuration file
├── run_python_script.bat    # Run script
└── mounting_detections/     # Folder for saved detections
```

## 📄 License

This project uses the GNU Affero General Public License v3.0 (AGPL-3.0). It is based on Ultralytics YOLO and is fully open source.

## 🙏 Acknowledgments

This project is made possible by the amazing [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) library. Their state-of-the-art computer vision technology forms the foundation for our AI detection of estrus behavior in cows.

**Thank you Ultralytics team!** 🚀 For making cutting-edge AI technology available that now also helps Dutch farmers.

## 🤝 Contributing

This is an open source project. You may modify and improve it as you see fit. Contributions are welcome via pull requests.

## 📞 Support

For questions or support, please contact via the project repository or community channels.

---
⚠️ Disclaimer

Use at your own risk.
This software is intended as a tool and does not replace professional knowledge and experience. The AI may give false notifications; the user remains responsible for the final assessment and decision. Physical inspection and identification of the animal remain essential.

Although this solution is designed to be user-friendly and efficient, the underlying technology is not new. The computer vision used is based on YOLO, a proven technique that has been applied for years for object and motion detection. The Telegram notifications also use an existing API. Despite appearing innovative, it involves a smart combination of existing technologies.
