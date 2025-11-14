@echo off
title cowcatcher

REM Configuration - modify these variables as needed
REM To see version conda in anaconda prompt = echo %CONDA_PREFIX%
set CONDA_PATH="C:\ProgramData\anaconda3\Scripts\activate.bat"
set CONDA_ENV_NAME=your_environment_name
set PROJECT_DRIVE=F:
set PROJECT_FOLDER=your_project_folder_path_without_drive
set SCRIPT_NAME=your_script.py

REM Activate conda base environment
call %CONDA_PATH%

REM Activate specific conda environment
REM call conda activate %CONDA_ENV_NAME%

REM Navigate to project and execute script
%PROJECT_DRIVE%
cd %PROJECT_FOLDER%
python %SCRIPT_NAME%

pause
