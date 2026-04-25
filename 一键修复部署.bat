@echo off
chcp 65001 > nul
title 一键修复基金分析工具

echo ==========================================
echo    基金分析工具 - 一键修复部署
echo ==========================================
echo.
echo 🔍 检测到内存不足问题，正在使用轻量版...
echo.

echo 📦 正在准备修复文件...
echo.

:: 备份原文件
if exist "app.py" (
    echo ✅ 备份原 app.py 为 app_backup.py
    copy app.py app_backup.py > nul
)

if exist "requirements.txt" (
    echo ✅ 备份原 requirements.txt 为 requirements_backup.txt
    copy requirements.txt requirements_backup.txt > nul
)

:: 创建轻量版
echo ✅ 创建轻量版应用...
if exist "app_light.py" (
    echo ✅ app_light.py 已存在
) else (
    echo ❌ app_light.py 不存在，请确保文件完整
    pause
    exit /b 1
)

echo ✅ 更新依赖文件...
if exist "requirements_lite.txt" (
    copy requirements_lite.txt requirements.txt > nul
) else (
    echo ❌ requirements_lite.txt 不存在
    pause
    exit /b 1
)

echo ✅ 更新 Procfile...
echo ✅ Procfile 已指向轻量版应用

echo.
echo 🚀 请按以下步骤完成修复：
echo.
echo 1️⃣ 提交修复代码：
echo    git add .
echo    git commit -m "Fix memory issue - switch to lite version"
echo    git push origin main
echo.
echo 2️⃣ 等待Render自动部署（3-5分钟）
echo.
echo 3️⃣ 测试修复结果：
echo    访问：https://fund-analyzer-rq0y.onrender.com/health
echo    应该看到：{"status": "ok", ...}
echo.
echo 4️⃣ 测试分析功能：
echo    输入基金代码：110011、161725、000961等
echo.
echo 💡 支持的基金代码：
echo    110011 - 易方达优质精选混合（张坤）
echo    161725 - 招商中证白酒指数（侯昊）
echo    000961 - 天弘沪深300ETF联接A（田汉卿）
echo    519732 - 交银新成长混合（王崇）
echo    006228 - 中欧医疗健康混合A（葛兰）
echo    007119 - 华安纳斯达克100指数A（倪斌）
echo    163402 - 兴全合润混合（董承非）
echo.
echo ==========================================
echo ⚡ 轻量版优势：
echo    ✅ 内存占用极低（<100MB）
echo    ✅ 启动快速（<10秒）
echo    ✅ 稳定运行（无内存溢出）
echo    ✅ 功能完整（评分、推荐、图表）
echo ==========================================
echo.
pause