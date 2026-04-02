@echo off
chcp 65001 >nul
echo ====================================
echo Video Clip Splitter - Build Script
echo ====================================
echo.
echo 请选择打包方式：
echo.
echo [1] 单文件模式 (体积小，启动慢，不含 Playwright)
echo [2] 便携版模式 (体积大，启动快，完整功能) - 推荐
echo.
set /p CHOICE="请输入选项 (1/2): "

if "%CHOICE%"=="1" goto SINGLE_FILE
if "%CHOICE%"=="2" goto PORTABLE
echo 无效选项，使用便携版模式...
goto PORTABLE

:SINGLE_FILE
echo.
echo 使用单文件模式打包...
echo 注意：单文件模式不包含 Playwright 浏览器，即梦视频功能不可用
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.9+
    pause
    exit /b 1
)

:: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Build
echo [2/3] Building...
pyinstaller --onefile --windowed ^
    --name "VideoClipSplitter" ^
    --add-data "assets;assets" ^
    --hidden-import=PIL._tkinter_finder ^
    --collect-all customtkinter ^
    --collect-all moviepy ^
    main.py

:: Done
echo [3/3] Build completed!
echo.
echo Output: dist\VideoClipSplitter.exe
echo.
echo 注意：此版本需要用户自行安装 Playwright 浏览器才能使用即梦视频功能
echo.
pause
exit /b 0

:PORTABLE
echo.
echo 使用便携版模式打包...
call build_portable.bat
exit /b 0
