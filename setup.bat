@echo off
title F1 Dashboard Setup
color 0A

echo ===================================================
echo    🏎️  F1 Dashboard - Setup (Python 3.13 Compatible)
echo ===================================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo ❌ Python not found!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo.

echo Installing packages WITHOUT building from source...
echo This may take 2-3 minutes...
echo.

echo [1/4] Installing NumPy (pre-built)...
python -m pip install --only-binary :all: numpy
if errorlevel 1 (
    echo ⚠️ Trying alternative NumPy installation...
    python -m pip install numpy --no-build-isolation
)
echo.

echo [2/4] Installing Pandas (pre-built)...
python -m pip install --only-binary :all: pandas
if errorlevel 1 (
    echo ⚠️ Trying alternative Pandas installation...
    python -m pip install pandas --no-build-isolation
)
echo.

echo [3/4] Installing Dash...
python -m pip install dash
echo.

echo [4/4] Installing Plotly and Dash Bootstrap...
python -m pip install plotly dash-bootstrap-components
echo.

echo ===================================================
echo    Verifying Installation...
echo ===================================================
echo.

python -c "import dash; print('✅ Dash installed!')" 2>nul
if errorlevel 1 echo ❌ Dash NOT installed!

python -c "import plotly; print('✅ Plotly installed!')" 2>nul
if errorlevel 1 echo ❌ Plotly NOT installed!

python -c "import pandas; print('✅ Pandas installed!')" 2>nul
if errorlevel 1 echo ❌ Pandas NOT installed!

python -c "import numpy; print('✅ NumPy installed!')" 2>nul
if errorlevel 1 echo ❌ NumPy NOT installed!

python -c "import dash_bootstrap_components; print('✅ Dash Bootstrap installed!')" 2>nul
if errorlevel 1 echo ❌ Dash Bootstrap NOT installed!

echo.
echo ===================================================
echo    ✅ Setup Complete!
echo ===================================================
echo.
echo Now run: start.bat
echo.
pause