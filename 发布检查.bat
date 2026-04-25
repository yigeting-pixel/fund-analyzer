@echo off
chcp 65001 > nul
title 基金分析工具 - 发布检查

echo ==========================================
echo    基金分析工具 - 发布前检查清单
echo ==========================================
echo.

echo 📋 检查项目文件...
if exist "app.py" (
    echo ✅ app.py - 主程序文件
) else (
    echo ❌ app.py - 缺失主程序文件
    goto :error
)

if exist "requirements.txt" (
    echo ✅ requirements.txt - 依赖文件
) else (
    echo ❌ requirements.txt - 缺失依赖文件
    goto :error
)

if exist "Procfile" (
    echo ✅ Procfile - Render配置文件
) else (
    echo ❌ Procfile - 缺失Render配置文件
    goto :error
)

if exist "render.yaml" (
    echo ✅ render.yaml - Render部署配置
) else (
    echo ❌ render.yaml - 缺失Render部署配置
    goto :error
)

if exist "templates\index.html" (
    echo ✅ templates\index.html - 网页模板
) else (
    echo ❌ templates\index.html - 缺失网页模板
    goto :error
)

if exist "static" (
    echo ✅ static\ - 静态资源目录
) else (
    echo ❌ static\ - 缺失静态资源目录
    goto :error
)

echo.
echo ✅ 所有核心文件检查通过！
echo.

echo 🔍 请确认以下信息：
echo 1. 你有GitHub账号吗？ (y/n)
set /p github_check=
if /i "%github_check%" neq "y" (
    echo ❌ 请先注册GitHub账号：https://github.com
    pause
    exit /b 1
)

echo 2. 你知道你的GitHub用户名吗？ (y/n)
set /p username_check=
if /i "%username_check%" neq "y" (
    echo ❌ 请登录GitHub查看你的用户名
    echo 用户名在GitHub右上角头像处显示
    pause
    exit /b 1
)

echo.
echo 🚀 准备就绪！现在可以开始发布了
echo.
echo 📖 详细步骤请查看：
echo    - 对外发布步骤.md（完整版）
echo    - 快速发布指南.txt（简化版）
echo.
echo 🌟 推荐使用快速发布指南（3步完成）
echo.
echo 按任意键打开快速发布指南...
pause > nul
notepad "快速发布指南.txt"

goto :end

:error
echo.
echo ❌ 文件检查失败，请确保项目文件完整
echo.
pause

:end