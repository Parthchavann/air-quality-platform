@echo off
echo Starting Air Quality Platform on Windows...

REM Navigate to project directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv_windows" (
    echo Creating Windows virtual environment...
    python -m venv venv_windows
)

REM Activate virtual environment
echo Activating virtual environment...
call venv_windows\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install streamlit pandas plotly

REM Run the simple dashboard
echo Starting Streamlit dashboard...
echo.
echo Dashboard will be available at: http://localhost:8506
echo.
streamlit run test_simple.py --server.port 8506

pause