# CowCatcher AI: Open Source & DIY 🐄💻

> **Welcome to the development branch!** Here you find exactly how it works. Here you can find the exact customized codes for the trained Cowcatcher model.

## 🎯 The Goal: Research, Test, Learn
We are shifting our focus. Instead of maintaining complex custom codebases, we are now fully dedicated to **research, testing, and community learning**. Learning from previously done researches regarding the subject. 
Our goal is not to write new software, but to understand how existing, powerful computer vision tools can be best applied in the stable. Here we provide the tools and data to replicate cowcatcher or build your own model.

---

## 🛠️ Based on the YOLO Standard
We don't reinvent the wheel. Everything here is based on the official **Ultralytics YOLO Train Settings**. It’s the gold standard for computer vision, and we use it to keep things transparent and easy to follow.

* **How we did it:** We took the standard YOLO framework and tuned it specifically for the stable—handling things like low light, dusty cameras, and identifying that specific mounting behavior.
* **Reproduction:** Every setting we used (epochs, image size, etc.) is right here in the code. If you run these scripts, you get the same CowCatcher results we do.

---

## 🏗️ Build or Replicate
Want to see if it actually works? Or maybe you want to train a "Local" model for your own specific cows?

1.  **Replicate:** Run our scripts to see exactly how we trained the model for mounting detection.
2.  **Customize:** Swap in your own footage to make a model that knows your barn inside out.
3.  **Validate:** Use the built-in YOLO tools to check the accuracy before you let it loose in the barn.

> **Bottom line:** We’re providing the blueprint. Whether you're here for research or run your model trained on your own data, the tools are yours.

## 🛠️ Requirements

### Bare minimum (for getting started)
- **Standard computer**
- **any IP camera** with RTSP support
- **Internet connection**

### Hardware (for best performance)
- **Computer** with NVIDIA graphics card (€600-1000 for 1-4 cameras)
- **any IP camera** with RTSP support (€80-170)
- **PoE switch** for cameras (€80 for 4 ports)
- **LAN cables** (€1 per meter)
- **Internet connection**
- **Scalable** more cameras require more powerful computer

### Software
- Our Cowcatcher AI software
- Anaconda Prompt
- Sublime Text or Visual Studio Code 
- WinRAR/7-Zip for extracting files

## 📥 Installation

### First of All

You can install this yourself by following the guide below, or contact me for assistance, i can also do the installation for free
- **Email:** jacobsfarmsocial@gmail.com
- **Telegram:** @Jacob5456

For additional guidance, I've created video tutorials for the installation process. While they aren't completely up-to-date, they're quite helpful as the process is largely the same.

**Video Playlist:**  
https://www.youtube.com/playlist?list=PLAa1RFX0i2uCmmDactfR1bR208mwl6KY0

### Step 1: Download Software
1. Download and install [Anaconda](https://www.anaconda.com/products/distribution)
2. Download and install [Sublime Text](https://www.sublimetext.com/) (optional)
3. Download and install [WinRAR](https://www.win-rar.com/) or 7-Zip
4. Download the latest release of [CowCatcherAI](https://github.com/CowCatcherAI/CowCatcherAI/releases)  
   or with command: `git clone -b Dev https://github.com/CowCatcherAI/CowCatcherAI.git`

### Step 2: Prepare Project
1. Extract the zip file to a folder of your choice (e.g., `C:\Users\username\Documents\Cowcatcherai`)
2. Remember the path to this folder, you'll need to reference it constantly

### Step 3: Set Up Python Environment

Open **Anaconda Prompt** and execute the following commands:

```bash
# Navigate to your project drive (replace C: with your drive)
C:

# Go to your project folder
cd \Users\username\Documents\Cowcatcher

# Create a new conda environment
conda create -n cowcatcher python=3.11

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

### Step 5: (Only for Nvidia graphic Cards) Check GPU Support

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
├── LICENSE
├── README.md
├── dataset.yaml                    # Dataset configuration for training
├── config.py                       # Configuration settings
├── run_python_script.bat          # Quick startup script
├── models/
│   ├── CowcatcherVx.pt            # Main AI model file
│   └── yolo11m.pt                 # Optional YOLO base model
├── src/
│   ├── cowcatcher.py              # Main detection program
│   ├── train.py                   # Training script for YOLO/fine-tuning
│   ├── annotate_helper.py         # Image annotation utility
│   └── split_database.py          # Dataset splitting utility
├── data/
│   ├── mounting_detections/       # Raw detection results
│   ├── annotate/                  # Images to be annotated
│   ├── delete/                    # Images annotated
│   ├── annotated_images/          # Manually annotated images
│   ├── annotated_labels/          # Corresponding label files
│   ├── train/                     # Training dataset
│   │   ├── images/
│   │   └── labels/
│   ├── val/                       # Validation dataset
│   │   ├── images/
│   │   └── labels/
│   └── test/                      # Optional test dataset
│       ├── images/
│       └── labels/
```

## 📄 License

This project uses the GNU Affero General Public License v3.0 (AGPL-3.0). It is based on Ultralytics YOLO and is fully open source.
IMPORTANT NOTICE: This software/model is NOT authorized for commercial use or distribution.

## 🙏 Acknowledgments

This project is made possible by the amazing [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) library. Their state-of-the-art computer vision technology forms the foundation for our AI detection of estrus behavior in cows.

**Thank you Ultralytics team!** 🚀 For making cutting-edge AI technology available that now also helps Dutch farmers.

## 🤝 Contributing

This is an open source project. You may modify and improve it as you see fit. Contributions are welcome via pull requests.

## 📞 Support

For questions or support, please contact via the project repository or community channels, we have a page on facebook https://www.facebook.com/groups/1765616710830233 and Telegram https://t.me/+SphG4deaWVNkYTQ8
For more direct contact: cowcatcherai@gmail.com

---
⚠️ Disclaimer

Use at your own risk.
This software is intended as a tool and does not replace professional knowledge and experience. The AI may give false notifications; the user remains responsible for the final assessment and decision. Physical inspection and identification of the animal remain essential.

Although this solution is designed to be user-friendly and efficient, the underlying technology is not new. The computer vision used is based on YOLO, a proven technique that has been applied for years for object and motion detection. The Telegram notifications also use an existing API. Despite appearing innovative, it involves a smart combination of existing technologies.
