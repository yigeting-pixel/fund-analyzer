@echo off
chcp 65001 > nul
title 快速修复内存问题

echo ==========================================
echo    快速修复 - 内存问题解决方案
echo ==========================================
echo.

echo 🔍 当前状态：仍在运行原版（内存不足）
echo 🎯 目标：切换到轻量版（稳定运行）
echo.

echo 📋 请按顺序执行以下步骤：
echo.

echo 1️⃣ 确认文件准备：
if exist "app_light.py" (
    echo ✅ app_light.py - 已准备
) else (
    echo ❌ app_light.py - 缺失
    pause
    exit /b 1
)

if exist "requirements_lite.txt" (
    echo ✅ requirements_lite.txt - 已准备
) else (
    echo ❌ requirements_lite.txt - 缺失
    pause
    exit /b 1
)

echo.

echo 2️⃣ 重命名应用文件：
echo 📝 将 app.py 重命名为 app_backup.py
echo 📝 将 app_light.py 重命名为 app.py
echo.
set /p rename_confirm=确认执行重命名操作？(y/n):
if /i "%rename_confirm%" neq "y" (
    echo ❌ 操作取消
    pause
    exit /b 1
)

:: 执行重命名
if exist "app.py" (
    ren app.py app_backup.py
    echo ✅ app.py → app_backup.py
)

if exist "app_light.py" (
    ren app_light.py app.py
    echo ✅ app_light.py → app.py
)

echo.

echo 3️⃣ 更新依赖文件：
copy requirements_lite.txt requirements.txt > nul
echo ✅ requirements.txt 已更新为轻量版

echo.

echo 4️⃣ 提交并部署：
echo 🚀 请在项目目录中执行以下Git命令：
echo.
echo git add .
echo git commit -m "紧急修复：切换到轻量版解决内存问题"
echo git push origin main
echo.
echo ⏳ 等待3-5分钟自动部署...
echo.

echo 5️⃣ 验证修复结果：
echo 🔗 访问：https://fund-analyzer-rq0y.onrender.com/
echo 📱 测试分析功能，输入：110011
echo ✅ 应该正常工作，不再崩溃
echo.

echo ==========================================
echo 💡 轻量版特点：
echo    - 内存占用：＜100MB
echo    - 支持基金：7只热门基金
echo    - 完整功能：评分、推荐、图表
echo    - 稳定运行：无内存溢出
echo ==========================================
echo.
echo ⚠️  重要提示：
echo    如果仍然看到内存错误，
echo    请在Render控制台重启服务
echo ==========================================
echo.
pause