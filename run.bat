@echo off
chcp 65001 >nul
echo ========================================
echo   SMART LOCK - QUICK LAUNCHER
echo ========================================
echo 1. Chạy Backend FastAPI (Uvicorn)
echo 2. Chạy Web Admin (Vite Dev Server)
echo 3. Chạy Menu Quản lý (manage.py)
echo ========================================
set /p choice="Chọn chức năng (1-3): "

if "%choice%"=="1" (
    echo Đang khởi động Backend...
    cd /d %~dp0backend
    call venv\Scripts\activate
    uvicorn app.main:app --reload
) else if "%choice%"=="2" (
    echo Đang khởi động Web Admin...
    cd /d %~dp0webapp\admin
    npm run dev
) else if "%choice%"=="3" (
    echo Đang mở Menu quản lý DB...
    cd /d %~dp0backend
    call venv\Scripts\activate
    python manage.py
) else (
    echo Lựa chọn không hợp lệ!
)
pause