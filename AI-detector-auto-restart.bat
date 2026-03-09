@echo off
title AI Detector Auto-Restart
:loop
echo --------------------------------------------------
echo [INFO] AI-detector started on %date% at %time%
echo --------------------------------------------------
"aidetector.exe" 
echo AI gecrasht, restarting in 20 seconds...
timeout /t 20
goto loop
