@echo off
REM Configuration - modify these variables as needed
REM To see version conda in anaconda prompt = echo %CONDA_PREFIX%
set CONDA_PATH="C:\ProgramData\anaconda3\Scripts\activate.bat" 
set PROJECT_DRIVE=F:
set PROJECT_FOLDER=your_project_folder_path_without_drive
set SCRIPT_NAME=your_script.py

REM Execute the script
call %CONDA_PATH%
%PROJECT_DRIVE%
cd %PROJECT_FOLDER%
python %SCRIPT_NAME%
pause
