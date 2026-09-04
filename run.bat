@echo off
chcp 65001 >nul
echo ========================================
echo   SMART LOCK - AUTO LAUNCHER ALL
echo ========================================
echo Đang tự động khởi động Backend và Web Admin...

:: 1. Khởi động Backend FastAPI trong cửa sổ riêng
start "Smart Lock Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && uvicorn app.main:app --reload"

:: 2. Khởi động Web Admin trong cửa sổ riêng
start "Smart Lock Web Admin" cmd /k "cd /d %~dp0webapp\admin && npm run dev"

echo.
echo ========================================
echo TẤT CẢ ĐÃ ĐƯỢC MỞ TỰ ĐỘNG!
echo ========================================
echo - Backend API: http://127.0.0.1:8000/docs
echo - Web Admin:   http://localhost:5173
echo.
pause