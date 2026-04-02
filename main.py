# -*- coding: utf-8 -*-
"""
视频片段拆分工具
主程序入口

功能：
1. 用户输入视频描述或旁白
2. 调用AI API拆分成5-15秒片段的提示词
3. 支持上传人物图片、场景图片、声线素材
4. 片段表格展示和编辑
5. 视频九宫格生成

作者：AI Assistant
版本：1.0.0
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk


def main():
    """主函数"""
    # 设置便携版环境（在导入其他模块之前）
    try:
        from core.portable_utils import setup_portable_env
        env_status = setup_portable_env()
        if env_status.get("playwright"):
            print("[便携版] Playwright 浏览器已配置")
        if env_status.get("ffmpeg"):
            print("[便携版] FFmpeg 已配置")
    except Exception as e:
        print(f"[便携版] 环境配置失败: {e}")

    # 设置外观模式
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # 导入主窗口（延迟导入以加快启动）
    from gui.main_window import MainWindow

    # 创建并运行应用
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()