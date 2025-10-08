# Camera and Telegram Bot Configuration File
# Fill in your personal camera details below

# RTSP URLs for cameras
# Camera 1 - position?
RTSP_URL_CAMERA1 = "rtsp://admin:YourPassword123@192.168.178.21:554/h264Preview_01_sub"
# Camera 2 - position?
#RTSP_URL_CAMERA2 = "rtsp://admin:YourPassword123@192.168.178.22:554/h264Preview_01_sub"

# Adding more cameras - copy and fill in rtsp://
# RTSP_URL_CAMERA3 = "rtsp://admin:YourPassword123@192.168.178.25:554/h264Preview_01_sub"
# RTSP_URL_CAMERA4 = "rtsp://admin:YourPassword123@192.168.178.26:554/h264Preview_01_sub"

# Computervision model version
MODEL_PATH = "CowcatcherV14.pt"

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather on Telegram
TELEGRAM_CHAT_IDS = ["PRIMARY_CHAT_ID", "SECONDARY_CHAT_ID", "THIRD_CHAT_ID"]  # Add multiple users - Get ID from @userinfobot

# Network Configuration Examples:
# Dont forget to enable RTSP streaming in camera software
# Local network: 192.168.178.x
# Port 554 is standard for RTSP
# For dual lens cameras: change channel number from 01→02 or 1→2 to access second lens
# Use substream for lower bandwidth/recording
# Use mainstream for higher quality live viewing

# Common RTSP endpoints for different camera brands:
# Reolink cameras: /h264Preview_01_sub (substream) or /h264Preview_01_main (mainstream)
# Dahua cameras: /cam/realmonitor?channel=1&subtype=0 (sub) or /cam/realmonitor?channel=1&subtype=1 (main)
# Hikvision cameras: /Streaming/Channels/101 (sub) or /Streaming/Channels/1 (main)
# Axis cameras: /axis-media/media.amp?videocodec=h264 or /mjpg/video.mjpg
# Foscam cameras: /videoMain or /videoSub
# TP-Link Tapo: /stream1 (main) or /stream2 (sub)
# Amcrest cameras: /cam/realmonitor?channel=1&subtype=0 (same as Dahua)
# Uniview cameras: /unicast/c1/s0/live (main) or /unicast/c1/s2/live (sub)
# Annke cameras: /Streaming/Channels/101 (same as Hikvision)
# Swann cameras: /h264Preview_01_sub or /cam/realmonitor?channel=1&subtype=0
# Lorex cameras: /h264Preview_01_sub (same as Reolink)
# Zmodo cameras: /videostream.cgi?loginuse=admin&loginpas=PASSWORD
# D-Link cameras: /live1.sdp (main) or /live2.sdp (sub)
# Netgear Arlo: /live (requires different authentication)
# Eufy cameras: /flv?port=1935&app=bcs&stream=channel0_main.bcs
# Ring cameras: (proprietary protocol, requires Ring API)
# Wyze cameras: /live (requires firmware modification for RTSP)

