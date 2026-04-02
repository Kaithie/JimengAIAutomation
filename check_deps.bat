@echo off
chcp 65001 >nul
echo ====================================
echo 依赖检测与自动安装脚本
echo ====================================
echo.

:: 检测并安装 ffmpeg
echo [1/3] 检测 ffmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [!] ffmpeg 未安装
    echo.
    echo 请选择安装方式：
    echo   1. 使用 winget 自动安装（推荐，需要管理员权限）
    echo   2. 手动下载安装（将打开下载页面）
    echo   3. 跳过
    echo.
    set /p ffmpeg_choice="请输入选择 (1/2/3): "

    if "%ffmpeg_choice%"=="1" (
        echo 正在使用 winget 安装 ffmpeg...
        winget install ffmpeg --accept-package-agreements --accept-source-agreements
        echo 请重新打开命令行窗口后继续检测
    ) else if "%ffmpeg_choice%"=="2" (
        echo 正在打开 ffmpeg 下载页面...
        start https://ffmpeg.org/download.html
        echo 请下载后解压，将 bin 目录添加到系统 PATH
    ) else (
        echo 已跳过 ffmpeg 安装
    )
) else (
    echo [OK] ffmpeg 已安装
    ffmpeg -version | findstr "ffmpeg version"
)
echo.

:: 检测并安装 Playwright 浏览器
echo [2/3] 检测 Playwright 浏览器...
python -c "import playwright; print('playwright installed')" >nul 2>&1
if errorlevel 1 (
    echo [!] playwright 未安装，正在安装...
    pip install playwright
)

echo 检测 Playwright 浏览器引擎...
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop()" >nul 2>&1
if errorlevel 1 (
    echo [!] Playwright 浏览器未安装，正在安装 Chromium...
    playwright install chromium
    echo [OK] Chromium 安装完成
) else (
    echo [OK] Playwright 浏览器已就绪
)
echo.

:: 检测 VC++ 运行库
echo [3/3] 检测 Visual C++ 运行库...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Installed >nul 2>&1
if errorlevel 1 (
    echo [!] 未检测到 VC++ 运行库
    echo 正在打开 Microsoft Visual C++ 下载页面...
    start https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo 请下载并安装
) else (
    echo [OK] VC++ 运行库已安装
)
echo.

:: 检测 Python 依赖
echo ====================================
echo 检测 Python 依赖...
echo ====================================

pip install -r requirements.txt --quiet

echo.
echo ====================================
echo 依赖检测完成！
echo ====================================
echo.
echo 如果有新安装的依赖，建议：
echo   1. 重新打开命令行窗口（使 PATH 生效）
echo   2. 重新运行此脚本确认所有依赖已就绪
echo.
pause
