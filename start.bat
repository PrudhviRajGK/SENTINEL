@echo off
echo ╔══════════════════════════════════════════╗
echo ║   Sentinel - Enterprise Threat Intel    ║
echo ╚══════════════════════════════════════════╝
echo.
echo Starting Sentinel...
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt

REM Install React dependencies if needed
if not exist "sentinel-frontend\node_modules" (
    echo Installing React dependencies...
    cd sentinel-frontend
    call npm install
    cd ..
)

REM Start Flask backend
echo.
echo Starting Flask backend on http://localhost:5000...
start "Sentinel Backend" cmd /k python app.py

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start React frontend
echo Starting React frontend on http://localhost:3000...
cd sentinel-frontend
start "Sentinel Frontend" cmd /k npm start
cd ..

echo.
echo ╔══════════════════════════════════════════╗
echo ║          Sentinel is running!            ║
echo ╠══════════════════════════════════════════╣
echo ║  Backend:  http://localhost:5000         ║
echo ║  Frontend: http://localhost:3000         ║
echo ╚══════════════════════════════════════════╝
echo.
echo Close the terminal windows to stop services
pause
