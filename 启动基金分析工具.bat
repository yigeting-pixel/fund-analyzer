@echo off
chcp 65001 > nul
title 明星基金经理分析系统

echo ==========================================
echo    明星基金经理分析系统 v1.0
echo ==========================================
echo.

:: 检查依赖
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [安装中] 正在安装依赖包，请稍候...
    pip install flask akshare pandas -q
    echo [完成] 依赖安装完毕
    echo.
)

:: 先停止旧的 Flask 进程（占用5000端口）
echo 正在停止旧进程...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 "') do (
    taskkill /F /PID %%a > nul 2>&1
)
timeout /t 1 /nobreak > nul

echo 正在启动服务...
echo 服务启动后，浏览器将自动打开分析界面
echo.
echo 关闭此窗口即停止服务
echo ==========================================

cd /d "%~dp0"

:: 延迟3秒后自动打开浏览器
start /b cmd /c "timeout /t 3 /nobreak > nul && start http://127.0.0.1:5000"

python app.py

pause
