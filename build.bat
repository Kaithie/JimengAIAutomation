@echo off
chcp 65001
echo ====================================
echo 视频片段拆分工具 - 打包脚本
echo ====================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt
pip install pyinstaller

:: 打包
echo [2/3] 开始打包...
pyinstaller --onefile --windowed ^
    --name "视频片段拆分工具" ^
    --add-data "assets;assets" ^
    --hidden-import=PIL._tkinter_finder ^
    --collect-all customtkinter ^
    --collect-all moviepy ^
    main.py

:: 完成
echo [3/3] 打包完成！
echo.
echo 输出文件: dist\视频片段拆分工具.exe
echo.
pause