# 🐄 CowCatcher AI
### Automatic Heat Detection for Dairy Farms

CowCatcher AI watches your barn cameras 24/7 and sends you a photo alert the moment a cow shows mounting behavior — the primary sign of estrus (heat). No more missed heats. No more checking cameras manually.

> **Powered by [AI Detector](https://github.com/eschouten/ai-detector)** — all video processing happens locally on your farm. No footage is ever sent to the cloud.

![CowCatcher Overview](https://github.com/user-attachments/assets/cee1e5f5-f9ae-4241-b8ad-8a9313b4a70c)

---

## ✨ Key Features

- **Instant Telegram alerts** — get a photo on your phone the moment it happens
- **24/7 monitoring** — works day and night (with a night-vision camera)
- **Completely private** — all processing runs on your own computer, nothing goes to the cloud
- **Free & open-source** — you only pay for your own hardware

---

## 🎯 Try It Without Installing

Curious to see the AI in action? Test the model directly in your browser — no installation needed:

👉 **[Try CowCatcher AI on HuggingFace](https://huggingface.co/spaces/CowcatcherAI/CowCatcherAI)**

---

## 📹 Camera Setup Tips

The AI is only as good as the video it sees. For best results:

- **Height:** Mount cameras **4–5 meters high** for a clear overhead view
- **Angle:** Aim slightly downward (~45°). Avoid flat side-on views where cows hide behind each other
- **Night vision:** Make sure the area is lit at night, or use a camera with IR night vision
- **Resolution:** 1080p recommended. Avoid pointing cameras directly at bright windows or sunlight
- **Connection:** Wired (LAN) cameras are more reliable than Wi-Fi for video streaming

---

## 🛠️ What You Need

### Hardware

| Component | Requirement |
| :-------- | :---------- |
| **Computer** | Any Windows PC. An NVIDIA GPU or any modern AMD/Intel GPU is recommended. No GPU → use the [Docker version](#-docker-advanced--older-gpus-or-linuxnas) below. |
| **Camera** | Any IP camera with **RTSP support**. Wired connection recommended. |
| **Internet** | Only needed to send Telegram notifications. |

### Software

- **Telegram** app on your phone (free)
- **AI Detector** — the engine that runs CowCatcher (instructions below)

---

## 🚀 Setup Guide (Windows)

Follow these steps to get up and running in about 10 minutes.

---

### Step 1 — Set Up Telegram Notifications

You need a Telegram "bot" to send alerts to your phone.

1. Install Telegram on your phone and open it.
2. Search for **@BotFather** and start a chat.
3. Send the message `/newbot` and follow the prompts to name your bot (e.g. `MyFarmAlertBot`).
4. **Save the API token** it gives you — it looks like `123456:ABC-DEF1234...`
5. Search for **@userinfobot**, send `/start`, and **save your numeric ID** (e.g. `123456789`).

---

### Step 2 — Download the AI Engine

👉 **[Download from AI Detector Releases](https://github.com/ESchouten/ai-detector/releases)**

Pick the right file for your hardware:

| File | GPU | Use when... |
| :--- | :-- | :---------- |
| `aidetector-winml-onnx-<version>.exe` | Any modern GPU (AMD, Intel, NVIDIA) | You're not sure, or you don't have an NVIDIA card |
| `aidetector-nvidia-cuda130-<version>.exe` | NVIDIA RTX 3000 series or newer | You have a recent NVIDIA GPU |
| `aidetector-nvidia-cuda126-<version>.exe` | NVIDIA RTX 2000 series or older | You have an older NVIDIA GPU |
| `aidetector-osx-onnx-<version>` | macOS | You're on a Mac |

> **Not sure which to pick?** Start with `winml-onnx` — it works on any modern Windows PC.

📺 [Watch the installation video calvingcatchet model](https://www.youtube.com/watch?v=UtLdXChVMCE).

📺 [Watch the installation video (The steps are the same; just use the latest 0.6.0 model instead](https://youtu.be/Pf44ZvQtSYU).

---

### Step 3 — Create Your Configuration File

1. Create a new folder on your computer, e.g. `C:\CowCatcher`
2. Move the downloaded file into that folder
3. In that same folder, create a new text file called [config.json](cci:7://file:///Users/erik/Projects/ESchouten/ai-detector/detector/config.json:0:0-0:0)
4. Paste in the following template and fill in your values:

```json
{
  "detectors": [
    {
      "detection": {
        "source": [
          "rtsp://admin:<YOUR_CAMERA_PASSWORD>@<YOUR_CAMERA_IP>:554/h264Preview_01_sub"
        ]
      },
      "yolo": {
        "model": "https://github.com/CowCatcherAI/CowCatcherAI/releases/download/model-V16/cowcatcherV15.2.onnx",
        "confidence": 0.85,
        "frames_min": 4,
        "timeout": 6,
        "time_max": 50
      },
      "exporters": {
        "telegram": {
          "token": "<YOUR_BOT_TOKEN>",
          "chat": "<YOUR_CHAT_ID>",
          "alert_every": 5,
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

**Replace these placeholders:**
- `<YOUR_CAMERA_IP>` — the IP address of your camera (e.g. `192.168.1.50`)
- `<YOUR_CAMERA_PASSWORD>` — your camera's password
- `<YOUR_BOT_TOKEN>` — the token from Step 1
- `<YOUR_CHAT_ID>` — your numeric ID from Step 1

> Don't know your camera's RTSP URL? Check the [Camera RTSP Reference](#-camera-rtsp-url-reference) below.

---

### Step 4 — Run

Double-click the `.exe` file. A terminal window opens showing detection logs. If text is scrolling and there are no red errors, everything is working!

> **Tip:** Keep the terminal window open while the detector is running. If it closes immediately, there is an error in your [config.json](cci:7://file:///Users/erik/Projects/ESchouten/ai-detector/detector/config.json:0:0-0:0) — check for missing quotes `"` or commas `,`.

---

## 📷 Camera RTSP URL Reference

Replace `[IP]` with your camera's IP address and `[PASS]` with its password. Default username is `admin` and port is `554`.

| Brand | Stream | RTSP URL |
| :---- | :----- | :------- |
| **Reolink** | Main | `rtsp://admin:[PASS]@[IP]:554/h264Preview_01_main` |
| | Sub | `rtsp://admin:[PASS]@[IP]:554/h264Preview_01_sub` |
| **Dahua / Amcrest** | Main | `rtsp://admin:[PASS]@[IP]:554/cam/realmonitor?channel=1&subtype=0` |
| | Sub | `rtsp://admin:[PASS]@[IP]:554/cam/realmonitor?channel=1&subtype=1` |
| **Hikvision / Annke** | Main | `rtsp://admin:[PASS]@[IP]:554/Streaming/Channels/1` |
| | Sub | `rtsp://admin:[PASS]@[IP]:554/Streaming/Channels/101` |
| **Axis** | H.264 | `rtsp://admin:[PASS]@[IP]:554/axis-media/media.amp?videocodec=h264` |
| **TP-Link Tapo** | Main | `rtsp://admin:[PASS]@[IP]:554/stream1` |
| | Sub | `rtsp://admin:[PASS]@[IP]:554/stream2` |
| **Foscam** | Main | `rtsp://admin:[PASS]@[IP]:554/videoMain` |
| | Sub | `rtsp://admin:[PASS]@[IP]:554/videoSub` |
| **Uniview** | Main | `rtsp://admin:[PASS]@[IP]:554/unicast/c1/s0/live` |
| | Sub | `rtsp://admin:[PASS]@[IP]:554/unicast/c1/s2/live` |
| **D-Link** | Main | `rtsp://admin:[PASS]@[IP]:554/live1.sdp` |
| **Wyze** | Main | `rtsp://admin:[PASS]@[IP]:554/live` |
| **Ctronic** | Main | `rtsp://admin:[PASS]@[IP]:554/11` |

> **Not listed?** Search `"[your camera brand] RTSP URL"`, or test your stream in **VLC** → *Media → Open Network Stream*.
>
> **NVR users:** The IP and password are usually the same for all cameras. Only the path changes (e.g. `h264Preview_01_main`, `h264Preview_02_main`).

---

## ⚙️ Fine-Tuning

### Adjusting Sensitivity

Tweak the [confidence](cci:1://file:///Users/erik/Projects/ESchouten/ai-detector/detector/src/aidetector/utils/config.py:184:0-189:28) value in the [yolo](cci:1://file:///Users/erik/Projects/ESchouten/ai-detector/detector/src/aidetector/detection/detector.py:166:4-217:41) section of your [config.json](cci:7://file:///Users/erik/Projects/ESchouten/ai-detector/detector/config.json:0:0-0:0):

| Value | Effect |
| :---- | :----- |
| `0.86` or lower | More sensitive — catches more, but may send false alerts |
| **`0.87`** | **Balanced — recommended starting point** |
| `0.88` or higher | Stricter — fewer false alerts, but may miss quick mounts |

Restart the application after saving changes.

### Multiple Cameras

Add a second camera by extending the `source` list:

```json
"source": [
  "rtsp://admin:password@192.168.1.50:554/h264Preview_01_sub",
  "rtsp://admin:password@192.168.1.51:554/h264Preview_01_sub"
]
```

---

## ❓ Troubleshooting

**The window opens and closes immediately**
There is likely a syntax error in your [config.json](cci:7://file:///Users/erik/Projects/ESchouten/ai-detector/detector/config.json:0:0-0:0). Check that:
- Every `"` and `,` is in the right place
- The model URL is plain text, not a formatted hyperlink

**"Connection Failed" errors**
- Make sure your computer and camera are on the same network
- Test your RTSP URL in **VLC** → *Media → Open Network Stream*
- Make sure RTSP/ONVIF is enabled in your camera's settings app

**Not getting Telegram messages**
- Double-check your bot token and chat ID
- Make sure you started the bot by sending it `/start` in Telegram

---

## 🐳 Docker (Advanced — older GPUs or Linux/NAS)

Use Docker if you have no GPU, or want to run this on a server or NAS.

**Requirements:** Docker Compose + NVIDIA Container Toolkit (for GPU support)

1. Create a `compose.yml` file:

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

2. Place your [config.json](cci:7://file:///Users/erik/Projects/ESchouten/ai-detector/detector/config.json:0:0-0:0) in the same folder
3. Run:

```bash
docker compose up -d
docker compose logs -f aidetector
```

---

## 🤝 Community & Support

- 💬 **Facebook:** [CowCatcher AI Group](https://www.facebook.com/groups/1765616710830233)
- 📱 **Telegram:** [CowCatcher AI Chat](https://t.me/+SphG4deaWVNkYTQ8)
- 📧 **Email:** [cowcatcherai@gmail.com](mailto:cowcatcherai@gmail.com)

---

## 📄 License

Licensed under **AGPL-3.0**, built on top of [Ultralytics YOLO](https://github.com/ultralytics/ultralytics).

> This software and trained model are **not authorized for commercial use or redistribution** without explicit permission.

## ⚠️ Disclaimer

This software is provided "as is" without warranty of any kind. It is an assistive tool — **not a substitute for professional veterinary advice**. Always confirm detections and consult a veterinarian for animal health decisions. The authors accept no liability for missed detections, false alarms, or decisions made based on this software.
