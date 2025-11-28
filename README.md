# 🐄 CowCatcher AI

### Automated Estrus Detection for Modern Dairy Farming

**CowCatcher AI** is an open-source computer vision system designed to monitor your herd 24/7. By analyzing live footage from your barn cameras, it automatically detects "mounting" behavior—the primary sign of estrus (heat)—and instantly sends a photo notification to your smartphone via Telegram or combine it with your Home assistant setup.

> **Powered by** [**eschouten/ai-detector**](https://github.com/eschouten/ai-detector)
> This project utilizes the robust AI detection engine built by E. Schouten to run our custom-trained CowCatcher models.

![CowCatcher Overview](https://github.com/user-attachments/assets/cee1e5f5-f9ae-4241-b8ad-8a9313b4a70c)

---

## ⚙️ How It Works

The system acts as a tireless digital herdsman. It processes video streams locally on your farm and only notifies you when action is required.

📷 barn camera footage ──→ 🤖 AI Computer Vision ──→ ⚡ mounting detection ──→ 💽 save image ──→ 📲 Telegram notification with image

## ✨ Key Features

* **Easy Deployment:** No Python, Anaconda, or complex environments to install. Just download and run.
* **24/7 Monitoring:** Never miss a heat, even during the night.
* **Instant Alerts:** Get direct notifications with image proof sent to your phone.
* **Data Privacy:** All video processing happens **locally** on your machine. No video is sent to the cloud.
* **Cost Effective:** Free, open-source software. You only pay for your hardware.

---

## 📹 Camera Setup & Best Practices
**Crucial:** The AI is only as good as the video feed. For the best results:

* **Height:** Mount cameras **3-4 meters high** to get a clear view over the cows.
* **Angle:** A downward angle (approx 45°) works best. Avoid flat, horizontal views where cows hide behind one another.
* **Lighting:** Ensure the area is lit at night, or use a camera with strong IR (Night Vision).
* **Coverage:** 1080p resolution is recommended. Avoid placing cameras facing directly into bright windows/sunlight.

---

## 🛠️ System Requirements

To run the AI models in real-time, specific hardware is required.

### Hardware
| Component | Requirement |
| :--- | :--- |
| **Graphics Card (GPU)** | **NVIDIA GTX 16-series or newer** (e.g., GTX 1660, RTX 2060, RTX 3060). <br> *Note: Older cards (e.g., GTX 10-series) must use the Docker version.* |
| **Camera** | Any IP Camera with **RTSP support**. |Optimal is connect with Lan-cables, wifi cams do work but are noticable slower and do miss frames.
| **Internet** | Required only for sending Telegram notifications. |

### Software
* **Telegram App:** Installed on your phone.
* **AI Detector:** The executable engine (instructions below).

---

## 🚀 Installation Guide (Windows)

Follow these four steps to get up and running in minutes.

### Step 1: Setup Telegram Notifications
You need a "Bot" to send you messages.
1.  Open Telegram and search for **@BotFather**.
2.  Send the message `/newbot`.
3.  Follow the prompts to name it (e.g., `MyFarmAlertBot`).
4.  **Copy the API Token** provided (It looks like `123456:ABC-DEF1234...`).
5.  Search for **@userinfobot** in Telegram and send `/start`.
6.  **Copy your ID** (It is a number like `123456789`).

### Step 2: Download the Engine
Download the latest `aidetector.exe` from the repository that powers this tool:
👉 **[Download from AI Detector Releases](https://github.com/ESchouten/ai-detector/releases)**

** link naar de uitleg video over de installatie https://youtu.be/MvbdJx7C3mM 

### Step 3: Configure the System
1.  Create a new folder on your computer (e.g., `C:\CowCatcher`).
2.  Move `aidetector.exe` into this folder.
3.  Create a new text file in that folder named `config.json`.
4.  Paste the following code into that file:

```json
{
    "detectors": [
        {
            "model": "https://github.com/CowCatcherAI/CowCatcherAI/releases/download/modelv-14/cowcatcherV15.pt",
            "sources": [
                "rtsp://admin:YourPassword123@192.168.100.22:554/h264Preview_01_sub"
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
                    "confidence": 0.87
                },
                "disk": {
                    "directory": "mounts"
                }
            }
        }
    ]
}
```

**Important Edits:**
* **Token & Chat:** Replace `YOUR_BOT_TOKEN_HERE` and `YOUR_USER_ID_HERE` with your values from Step 1.
* **Camera Source:** Replace the `rtsp://...` URL with your camera's specific address.
    * *Tip: If you don't know your RTSP URL, check your camera manual or use a tool like "iSpy Connect Database" to find the format for your camera brand.*

### Step 4: Run
Double-click `aidetector.exe`. A black terminal window will open showing the detection logs. If you see text scrolling and no errors, the system is live!

---

## 📋 Configuration Reference

The `config.json` file controls the behavior of the AI detector. Here is a breakdown of the available fields:

| Field | Description |
| :--- | :--- |
| **`detectors`** | A list of detector configurations. You can define multiple detectors for different cameras. |
| **`model`** | The URL or local path to the YOLO model weights (`.pt` file). |
| **`sources`** | A list of input sources. Typically a single RTSP URL (e.g., `rtsp://...`) or a local video file path. |

### Detection Settings (`detection`)
| Field | Default | Description |
| :--- | :--- | :--- |
| **`confidence`** | `0.7` | Minimum certainty (0.0 - 1.0) for a frame to count as a detection. |
| **`frames_min`** | `1` | Minimum number of positive frames required to trigger an event. |
| **`timeout`** | `None` | Seconds of "silence" (no detection) before an event is considered finished. |
| **`time_max`** | `60` | Maximum duration (in seconds) for a single event window. |

### Exporters (`exporters`)
Defines where the results are sent. All exporters can be a single object or an array of objects.
*   **`telegram`**: Sends notifications to your phone.
    *   `token`: Telegram Bot token.
    *   `chat`: Telegram Chat ID.
    *   `confidence`: (Optional) Specific confidence threshold for Telegram alerts.
*   **`disk`**: Saves images locally.
    *   `directory`: Folder name for saving images.
    *   `confidence`: (Optional) Specific confidence threshold for saving images.

---

## ⚙️ Fine-Tuning & Advanced Setup

### Adjusting Sensitivity
If the AI is missing heats or sending false alarms, adjust the `"confidence"` value in your `config.json`:
* **0.87 (Default):** Balanced.
* **0.86 or lower:** More sensitive (Detects more, but potential false alarms).
* **0.88 or higher:** Stricter (Fewer false alarms, but might miss quick mounts).
* *Note: You must restart the application after saving changes.*

### Using Multiple Cameras
To monitor multiple areas, you can add more detector blocks to your config.

<details>
<summary><b>Click here to view a Multi-Camera Config Example</b></summary>

```json
{
    "detectors": [
        {
            "model": "...",
            "sources": ["rtsp://192.168.1.50/stream1", "rtsp://192.168.1.52/stream1"],
            "detection": { ... },
            "exporters": { ... }
        }
    ]
}
```
</details>

---

## ❓ Troubleshooting

**The black window opens and closes immediately:**
This usually means there is a syntax error in your `config.json`.
* Ensure you didn't accidentally remove a quote `"` or a comma `,`.
* Ensure you pasted the **raw link** for the model, not a formatted link.

**I am getting "Connection Failed" errors:**
* Check that your computer is on the same network as the camera.
* Verify your RTSP stream URL in a media player like VLC to ensure it works.

**Frame detections are slow (200ms+):**
* Verify that NVIDIA drivers are installed and up to date.

---

## 🐳 Docker Usage (Advanced)

For users with older GPUs or those running home servers, we provide a Docker image.

**Prerequisites:** Docker Compose and the **NVIDIA Container Toolkit**.

1.  Create a `compose.yml` file:

```yaml
services:
  aidetector:
    image: "ghcr.io/eschouten/ai-detector:latest"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./detections:/app/detections
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [gpu]
```

2.  Place your `config.json` (from Step 3 above) in the same directory.
3.  Run the container:
    ```bash
    docker compose up -d
    ```

---

## 🤝 Community & Support

Need help setting up your camera URL or tuning the AI? Join our community of farmers and developers.

* **Facebook:** [CowCatcher AI Group](https://www.facebook.com/groups/1765616710830233)
* **Telegram:** [CowCatcher AI Chat](https://t.me/+SphG4deaWVNkYTQ8)
* **Email:** [cowcatcherai@gmail.com](mailto:cowcatcherai@gmail.com)

## 📄 License & Disclaimer

**License:** This project uses the **GNU Affero General Public License v3.0 (AGPL-3.0)**. It is built upon [Ultralytics YOLO](https://github.com/ultralytics/ultralytics).
* **Notice:** This software/model is **NOT** authorized for commercial use or distribution without permission.

**Disclaimer:**
> Use at your own risk. This software is intended as a supplementary tool and does not replace professional veterinary knowledge or human observation. The AI may generate false positives or negatives; the user remains responsible for all final breeding decisions.
