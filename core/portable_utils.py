# -*- coding: utf-8 -*-
"""
便携版路径处理工具
处理 PyInstaller 打包后的资源路径问题
"""

import os
import sys
import subprocess
from pathlib import Path


def get_base_path() -> Path:
    """
    获取应用基础路径

    PyInstaller 打包后，sys._MEIPASS 指向解压后的临时目录
    但对于便携版，我们需要使用 exe 所在的目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后：使用 exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境：使用项目根目录
        return Path(__file__).parent.parent


def get_internal_path() -> Path:
    """
    获取 _internal 目录路径（PyInstaller 打包后的资源目录）
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后，使用 sys._MEIPASS 获取资源目录
        # 这是 PyInstaller 解压资源的实际位置
        return Path(sys._MEIPASS)
    else:
        return get_base_path()


def get_playwright_browser_path() -> str:
    """
    获取 Playwright 浏览器路径

    Returns:
        浏览器路径字符串，如果找不到返回 None
    """
    base_path = get_base_path()
    internal_path = get_internal_path()

    # 可能的浏览器路径（按优先级排序）
    possible_paths = [
        # PyInstaller 打包后的路径（使用 sys._MEIPASS）
        internal_path / "playwright" / "driver" / "local-browsers" / "chromium",
        # 备选路径：exe 同级目录的 _internal
        base_path / "_internal" / "playwright" / "driver" / "local-browsers" / "chromium",
        # 标准 Playwright 路径
        internal_path / "playwright" / "driver" / "package" / ".local-browsers" / "chromium",
    ]

    for path in possible_paths:
        if path.exists():
            # 验证 chrome.exe 是否存在
            chrome_exe = path / "chrome-win64" / "chrome.exe"
            if chrome_exe.exists():
                print(f"[Playwright] 找到浏览器: {chrome_exe}")
                return str(path)
            else:
                print(f"[Playwright] 路径存在但缺少 chrome.exe: {path}")

    return None


def get_ffmpeg_path() -> str:
    """
    获取 FFmpeg 可执行文件路径

    Returns:
        ffmpeg.exe 路径，如果找不到返回 None
    """
    base_path = get_base_path()
    internal_path = get_internal_path()

    # 可能的 ffmpeg 路径
    possible_paths = [
        internal_path / "ffmpeg" / "ffmpeg.exe",
        base_path / "ffmpeg" / "ffmpeg.exe",
        # 也检查系统 PATH
        "ffmpeg",
    ]

    for path in possible_paths:
        if path != "ffmpeg":
            if path.exists():
                return str(path)
        else:
            # 检查系统 PATH
            import shutil
            if shutil.which("ffmpeg"):
                return "ffmpeg"

    return None


def setup_playwright_env():
    """
    设置 Playwright 环境变量
    让 Playwright 使用打包的浏览器
    """
    browser_path = get_playwright_browser_path()
    if browser_path:
        # PLAYWRIGHT_BROWSERS_PATH 应该指向包含 chromium 目录的父目录
        # 这样 Playwright 会查找: PLAYWRIGHT_BROWSERS_PATH/chromium/chrome-win64/chrome.exe
        browser_parent = str(Path(browser_path).parent)
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_parent
        print(f"[Playwright] 设置浏览器路径: {browser_parent}")
        print(f"[Playwright] 浏览器目录: {browser_path}")
        return True
    else:
        print("[Playwright] 未找到本地浏览器，将尝试使用系统默认浏览器")
        print(f"[Playwright] 内部资源路径: {get_internal_path()}")
        # 列出可能的位置帮助调试
        internal_path = get_internal_path()
        base_path = get_base_path()
        print(f"[Playwright] 检查路径:")
        print(f"  - {internal_path / 'playwright' / 'driver' / 'local-browsers' / 'chromium'}")
        print(f"  - {base_path / '_internal' / 'playwright' / 'driver' / 'local-browsers' / 'chromium'}")
    return False


def setup_ffmpeg_env():
    """
    设置 FFmpeg 环境变量
    让 moviepy 使用打包的 FFmpeg
    """
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path and ffmpeg_path != "ffmpeg":
        # 设置 FFmpeg 路径
        ffmpeg_dir = str(Path(ffmpeg_path).parent)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
        return True
    return False


def check_browser_dependencies() -> dict:
    """
    检查浏览器运行所需的系统依赖

    Returns:
        dict: 包含各项检查结果
    """
    results = {
        "chrome_found": False,
        "chrome_exe": None,
        "can_run": False,
        "error": None
    }

    browser_path = get_playwright_browser_path()
    if browser_path:
        results["chrome_found"] = True
        chrome_exe = Path(browser_path) / "chrome-win64" / "chrome.exe"
        results["chrome_exe"] = str(chrome_exe)

        # 尝试运行 chrome --version 检查是否能启动
        try:
            result = subprocess.run(
                [str(chrome_exe), "--version"],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                results["can_run"] = True
                results["version"] = result.stdout.decode().strip()
            else:
                results["error"] = f"Chrome 返回错误码: {result.returncode}"
        except subprocess.TimeoutExpired:
            results["error"] = "Chrome 启动超时"
        except FileNotFoundError:
            results["error"] = "Chrome 可执行文件不存在"
        except OSError as e:
            results["error"] = f"Chrome 无法启动: {e}\n可能缺少 Visual C++ 运行库，请安装 VC++ Redistributable"
        except Exception as e:
            results["error"] = f"未知错误: {e}"
    else:
        results["error"] = "未找到本地浏览器"

    return results


def setup_portable_env():
    """
    设置便携版环境
    在应用启动时调用
    """
    playwright_ok = setup_playwright_env()
    ffmpeg_ok = setup_ffmpeg_env()

    return {
        "playwright": playwright_ok,
        "ffmpeg": ffmpeg_ok
    }


if __name__ == "__main__":
    # 测试路径
    print(f"Base path: {get_base_path()}")
    print(f"Internal path: {get_internal_path()}")
    print(f"Playwright browser: {get_playwright_browser_path()}")
    print(f"FFmpeg: {get_ffmpeg_path()}")
