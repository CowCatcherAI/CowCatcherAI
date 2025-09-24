@echo off
title your_camera_name 
REM Configuration - modify these variables as needed
REM To see version conda in anaconda prompt = echo %CONDA_PREFIX%
set CONDA_PATH="C:\ProgramData\anaconda3\Scripts\activate.bat" 
set PROJECT_DRIVE=F:
set PROJECT_FOLDER=your_project_folder_path_without_drive
REM set SCRIPT_NAME=your_script.py

REM Navigate to project directory and activate environment
call %CONDA_PATH%
%PROJECT_DRIVE%
cd %PROJECT_FOLDER%
REM python %SCRIPT_NAME%

REM Show current location and open interactive command prompt
echo Anaconda environment activated in %cd%
cmd /k
