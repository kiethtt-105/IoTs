@echo off
chcp 65001 >nul
echo ========================================
echo   SMART LOCK - AUTO LAUNCHER ALL
echo ========================================
echo Dang tu dong khoi dong he thong...
echo.

:: 0. Dam bao MQTT Broker (Mosquitto) va PostgreSQL dang chay
net start mosquitto >nul 2>&1
net start postgresql-x64-18 >nul 2>&1

echo --- Kiem tra ket noi ---
powershell -NoProfile -Command "if((Test-NetConnection -ComputerName 127.0.0.1 -Port 1883 -WarningAction SilentlyContinue).TcpTestSucceeded){Write-Host 'MQTT (1883)       : OK' -ForegroundColor Green}else{Write-Host 'MQTT (1883)       : KHONG KET NOI DUOC' -ForegroundColor Red}"
powershell -NoProfile -Command "if((Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue).TcpTestSucceeded){Write-Host 'PostgreSQL (5432) : OK' -ForegroundColor Green}else{Write-Host 'PostgreSQL (5432) : KHONG KET NOI DUOC' -ForegroundColor Red}"
echo.

:: 1. Khoi dong Backend FastAPI trong cua so rieng
start "Smart Lock Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && uvicorn app.main:app --reload"

:: 2. Khoi dong Web Admin trong cua so rieng
start "Smart Lock Web Admin" cmd /k "cd /d %~dp0webapp\admin && npm run dev"

:: 3. Khoi dong Sensor Simulator trong cua so rieng
start "Smart Lock Sensor Simulator" cmd /k "cd /d %~dp0sensor-simulator && call venv\Scripts\activate && pip install requests && python src\main.py"

:: 4. Mo Menu quan ly (manage.py) trong cua so rieng
start "Smart Lock Manage" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python manage.py"

echo Dang cho Backend va Web Admin khoi dong (5 giay)...
timeout /t 5 /nobreak >nul

echo --- Kiem tra Backend / Web Admin ---
powershell -NoProfile -Command "if((Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -WarningAction SilentlyContinue).TcpTestSucceeded){Write-Host 'Backend API (8000): OK' -ForegroundColor Green}else{Write-Host 'Backend API (8000): CHUA SAN SANG, xem cua so Backend' -ForegroundColor Yellow}"
powershell -NoProfile -Command "if((Test-NetConnection -ComputerName 127.0.0.1 -Port 5173 -WarningAction SilentlyContinue).TcpTestSucceeded){Write-Host 'Web Admin (5173)  : OK' -ForegroundColor Green}else{Write-Host 'Web Admin (5173)  : CHUA SAN SANG, xem cua so Web Admin' -ForegroundColor Yellow}"

echo.
echo ========================================
echo TAT CA DA DUOC MO TU DONG!
echo ========================================
echo - MQTT Broker: localhost:1883
echo - Backend API: http://127.0.0.1:8000/docs
echo - Web Admin:   http://localhost:5173
echo - Manage.py:   cua so rieng da mo
echo.
pause