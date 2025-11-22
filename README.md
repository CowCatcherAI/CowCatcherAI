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

### Step 1: Create Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Give your bot a name: "e.g.:" `cowcatcher`
4. Give your bot a username: `cowcatcherBot`
5. **Save the API token** you receive, NEVER share this token

### Step 2: Get Your User ID
1. Search for `@userinfobot` in Telegram
2. Start a chat and send `/start`
3. **Note your personal Telegram ID**

### software as .exe and dockers will later be edited, otherwise check the Interactive_GUI branch for working program

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
