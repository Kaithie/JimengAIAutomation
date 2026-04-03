@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ====================================
echo Video Clip Splitter - Portable Build
echo ====================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)

:: Step 1: Install dependencies
echo [1/6] Installing dependencies...
pip install -r requirements.txt -q
pip install pyinstaller -q

:: Step 2: Install Playwright browsers
echo [2/6] Installing Playwright browser...
python -m playwright install chromium
if errorlevel 1 (
    echo [WARN] Playwright browser install failed, continuing...
)

:: Step 3: Build with onedir mode
echo [3/6] Building application...
pyinstaller --onedir --windowed --name "VideoClipSplitter" --add-data "assets;assets" --hidden-import=PIL._tkinter_finder --hidden-import=playwright.sync_api --hidden-import=playwright._impl._driver --collect-all customtkinter --collect-all moviepy --collect-all playwright --noupx main.py

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

:: Step 4: Copy Playwright browsers
echo [4/6] Copying Playwright browser...
set PLAYWRIGHT_CACHE=%LOCALAPPDATA%\ms-playwright
set DEST_BROWSER=dist\VideoClipSplitter\_internal\playwright\driver\local-browsers

if not exist "%DEST_BROWSER%" mkdir "%DEST_BROWSER%"

if exist "%PLAYWRIGHT_CACHE%" (
    for /d %%d in ("%PLAYWRIGHT_CACHE%\chromium-*") do (
        echo Copying: %%d
        xcopy "%%d" "%DEST_BROWSER%\chromium\" /E /I /Y /Q
    )
) else (
    echo [WARN] Playwright cache not found
)

:: Step 4.5: Copy VC++ Redistributable DLLs (required for Chrome)
echo [4.5/6] Copying VC++ runtime DLLs...
set CHROME_DIR=%DEST_BROWSER%\chromium\chrome-win64
set VC_REDIST=%SystemRoot%\System32

:: Copy common VC++ runtime DLLs that Chrome needs
for %%d in (VCRUNTIME140.dll VCRUNTIME140_1.dll MSVCP140.dll MSVCP140_1.dll MSVCP140_2.dll) do (
    if exist "%VC_REDIST%\%%d" (
        copy /Y "%VC_REDIST%\%%d" "%CHROME_DIR%\" >nul 2>&1
        echo   Copied: %%d
    )
)

:: Step 5: Copy FFmpeg (local first, then download)
echo [5/6] Setting up FFmpeg...
set "FFMPEG_DIR=dist\VideoClipSplitter\_internal\ffmpeg"
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"

if exist "%FFMPEG_DIR%\ffmpeg.exe" (
    echo FFmpeg already exists, skipping...
) else (
    :: Try local ffmpeg first (check common locations)
    set "LOCAL_FFMPEG="

    :: Check if ffmpeg is in PATH
    where ffmpeg.exe >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%i in ('where ffmpeg.exe') do set "LOCAL_FFMPEG=%%i"
    )

    :: Check common installation directories
    if not defined LOCAL_FFMPEG (
        for %%p in (
            "C:\ffmpeg\bin\ffmpeg.exe"
            "C:\Program Files\ffmpeg\bin\ffmpeg.exe"
            "%LOCALAPPDATA%\ffmpeg\bin\ffmpeg.exe"
            "%USERPROFILE%\ffmpeg\bin\ffmpeg.exe"
            "%USERPROFILE%\scoop\apps\ffmpeg\current\bin\ffmpeg.exe"
        ) do (
            if exist %%p (
                set "LOCAL_FFMPEG=%%p"
                goto :found_local
            )
        )
    )

    :found_local
    if defined LOCAL_FFMPEG (
        echo Found local FFmpeg: !LOCAL_FFMPEG!
        for %%i in ("!LOCAL_FFMPEG!") do set "FFMPEG_BIN_DIR=%%~dpi"
        echo Copying from: !FFMPEG_BIN_DIR!
        copy /Y "!FFMPEG_BIN_DIR!ffmpeg.exe" "%FFMPEG_DIR%\" >nul
        if exist "!FFMPEG_BIN_DIR!ffprobe.exe" copy /Y "!FFMPEG_BIN_DIR!ffprobe.exe" "%FFMPEG_DIR%\" >nul
        echo FFmpeg copied from local installation.
    ) else (
        echo Local FFmpeg not found, downloading...
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg_temp.zip' -UseBasicParsing"
        if exist ffmpeg_temp.zip (
            echo Extracting FFmpeg...
            powershell -Command "Expand-Archive -Path 'ffmpeg_temp.zip' -DestinationPath 'ffmpeg_extract' -Force; Copy-Item 'ffmpeg_extract\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe' '%FFMPEG_DIR%\' -Force; Copy-Item 'ffmpeg_extract\ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe' '%FFMPEG_DIR%\' -Force"
            del ffmpeg_temp.zip
            rmdir /s /q ffmpeg_extract
            echo FFmpeg downloaded and installed.
        )
    )
)

:: Step 6: Create README
echo [6/6] Creating readme...
echo ==================================== > dist\VideoClipSplitter\README.txt
echo Video Clip Splitter - Usage Guide >> dist\VideoClipSplitter\README.txt
echo ==================================== >> dist\VideoClipSplitter\README.txt
echo. >> dist\VideoClipSplitter\README.txt
echo Double-click VideoClipSplitter.exe to start. >> dist\VideoClipSplitter\README.txt
echo. >> dist\VideoClipSplitter\README.txt
echo Requirements: >> dist\VideoClipSplitter\README.txt
echo - Windows 10/11 64-bit >> dist\VideoClipSplitter\README.txt
echo - No Python installation needed >> dist\VideoClipSplitter\README.txt
echo. >> dist\VideoClipSplitter\README.txt
echo Keep the folder structure intact. >> dist\VideoClipSplitter\README.txt
echo Do not move the .exe file alone. >> dist\VideoClipSplitter\README.txt

echo.
echo ====================================
echo Build Complete!
echo ====================================
echo.
echo Output: dist\VideoClipSplitter
echo.
echo To distribute:
echo 1. Compress VideoClipSplitter folder to ZIP
echo 2. Send to users to extract and run
echo.
pause
