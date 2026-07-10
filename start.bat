@echo off
title F1 Dashboard
color 0A

echo ===================================================
echo    🏎️  F1 Visual Analytics Dashboard
echo ===================================================
echo.

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    echo.
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)
python --version
echo ✅ Python found
echo.

echo [2/5] Checking required packages...
python -c "import dash" 2>nul
if errorlevel 1 (
    echo ⚠️ Dash not found! Running setup...
    echo.
    call setup.bat
)
echo ✅ Packages ready
echo.

echo [3/5] Checking dashboard files...
if not exist "app.py" (
    echo ❌ app.py not found!
    echo.
    echo Current directory: %cd%
    echo Please make sure app.py is in this folder
    echo.
    pause
    exit /b 1
)
echo ✅ app.py found

if exist "data\master_f1_final_dnf_fixed.csv" (
    echo ✅ Data file found: master_f1_final_dnf_fixed.csv
) else (
    echo ⚠️ Data file not found!
    echo    Expected: data\master_f1_final_dnf_fixed.csv
    echo    Using sample data for testing.
)
echo.

echo [4/5] Checking port 8050...
netstat -ano | findstr ":8050" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo ✅ Port 8050 is available
) else (
    echo ⚠️ Port 8050 is in use!
    echo.
    echo To free the port, run:
    echo   taskkill /F /IM python.exe
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b
)
echo.

echo [5/5] Starting dashboard...
echo.
echo ===================================================
echo    🚀 Dashboard Starting...
echo ===================================================
echo.
echo 📊 Open in browser: http://localhost:8050
echo.
echo 💡 Tips:
echo    - Use filters to explore data
echo    - Hover over charts for details
echo    - Click legend to toggle drivers
echo    - Download charts using camera icon
echo.
echo ⏹️  Press Ctrl+C to stop the server
echo ===================================================
echo.

:: Run the dashboard
python app.py

:: If it crashes, show error
if errorlevel 1 (
    echo.
    echo ===================================================
    echo    ❌ Dashboard Crashed!
    echo ===================================================
    echo.
    echo Possible fixes:
    echo   1. Run setup.bat again
    echo   2. Check data file exists
    echo   3. Close other programs on port 8050
    echo   4. Check Python version: python --version
    echo   5. Try: python -m pip install --upgrade dash
    echo.
    pause
)

pause