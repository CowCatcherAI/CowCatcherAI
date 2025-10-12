#!/bin/bash

# CowCatcher AI Container Startup Script

echo "============================================"
echo "  CowCatcher AI - Starting..."
echo "============================================"

# Set working directory
cd /app

# Check if config exists, if not wait for user to configure via web UI
if [ ! -f /app/data/config.json ]; then
    echo ""
    echo "No configuration found!"
    echo "Please configure CowCatcher AI via the web UI"
    echo ""
    echo "Web UI will be available at:"
    echo "   - http://localhost:5000 (from host machine)"
    echo "   - http://$(hostname -i):5000 (from network)"
    echo ""
    echo "You will need:"
    echo "   1. Camera RTSP URL"
    echo "   2. Telegram Bot Token (from @BotFather)"
    echo "   3. Telegram Chat ID (from @userinfobot)"
    echo ""
    echo "Starting configuration web interface..."
    echo ""
    
    # Start only web UI in foreground
    exec python webui/webui.py
else
    echo "Configuration found, starting CowCatcher AI..."
    echo ""
    
    # Start web UI in background
    python webui/webui.py &
    WEBUI_PID=$!
    echo "Web UI started on port 5000 (PID: $WEBUI_PID)"
    echo "   Access at: http://localhost:5000"
    echo ""
    
    # Wait a moment for web UI to start
    sleep 2
    
    # Start cowcatcher in background
    echo "Starting CowCatcher detection system..."
    echo "============================================"
    echo ""
    python cowcatcher/cowcatcher.py &
    COWCATCHER_PID=$!
    echo "CowCatcher started (PID: $COWCATCHER_PID)"
    echo ""
    echo "Both services are now running!"
    echo "Web UI: http://localhost:5000"
    echo "Configure your camera and Telegram settings in the web UI"
    echo ""
    
    # Keep container running by waiting for web UI (which should stay up)
    wait $WEBUI_PID
fi
