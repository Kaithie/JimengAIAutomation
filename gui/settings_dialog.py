# -*- coding: utf-8 -*-
"""
设置对话框模块
"""

import customtkinter as ctk
from typing import Optional


class SettingsDialog(ctk.CTkToplevel):
    """设置对话框"""

    def __init__(self, parent, config_manager):
        super().__init__(parent)

        self.config_manager = config_manager
        self.result = False

        # 设置窗口
        self.title("⚙️ 设置")
        self.geometry("700x650")
        self.minsize(600, 500)
        self.resizable(True, True)

        # 居中显示
        self.transient(parent)
        self.grab_set()

        # 创建UI
        self._create_ui()

        # 加载当前配置
        self._load_config()

    def _create_ui(self):
        """创建UI"""
        # 创建滚动容器
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color=["#f8fafc", "#1e1e1e"]
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=(15, 15), pady=(15, 0))

        # 主容器
        self.main_container = self.scrollable_frame

        # 创建标签页
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 添加标签页
        self.api_tab = self.tabview.add("🔌 API 设置")
        self.prompt_tab = self.tabview.add("💬 提示词设置")

        # ==================== API 设置标签页 ====================
        # 平台选择
        platform_label = ctk.CTkLabel(self.api_tab, text="选择平台:")
        platform_label.pack(anchor="w", padx=10, pady=(10, 0))

        platforms = self.config_manager.PLATFORMS
        platform_names = [p["name"] for p in platforms.values()]
        platform_ids = list(platforms.keys())

        self.platform_var = ctk.StringVar(value=platform_names[0])
        self.platform_ids = platform_ids

        self.platform_menu = ctk.CTkOptionMenu(
            self.api_tab,
            values=platform_names,
            variable=self.platform_var,
            command=self._on_platform_change
        )
        self.platform_menu.pack(fill="x", pady=(5, 15), padx=10)

        # API Key
        key_label = ctk.CTkLabel(self.api_tab, text="API Key:")
        key_label.pack(anchor="w", padx=10)

        self.key_entry = ctk.CTkEntry(
            self.api_tab,
            placeholder_text="请输入API Key",
            show="*"
        )
        self.key_entry.pack(fill="x", pady=(5, 15), padx=10)

        # 显示/隐藏Key
        self.show_key_var = ctk.BooleanVar(value=False)
        self.show_key_check = ctk.CTkCheckBox(
            self.api_tab,
            text="显示API Key",
            variable=self.show_key_var,
            command=self._toggle_key_visibility
        )
        self.show_key_check.pack(anchor="w", pady=(0, 15), padx=10)

        # 端点URL
        endpoint_label = ctk.CTkLabel(self.api_tab, text="端点URL:")
        endpoint_label.pack(anchor="w", padx=10)

        self.endpoint_entry = ctk.CTkEntry(
            self.api_tab,
            placeholder_text="自定义端点URL（可选）"
        )
        self.endpoint_entry.pack(fill="x", pady=(5, 15), padx=10)

        # 模型输入（改为手动填写）
        model_label = ctk.CTkLabel(self.api_tab, text="模型:")
        model_label.pack(anchor="w", padx=10)

        self.model_entry = ctk.CTkEntry(
            self.api_tab,
            placeholder_text="输入模型名称，如 qwen-max、gpt-4o"
        )
        self.model_entry.pack(fill="x", pady=(5, 15), padx=10)

        # 平台提示信息
        self.platform_hint = ctk.CTkLabel(
            self.api_tab,
            text="",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            wraplength=450
        )
        self.platform_hint.pack(anchor="w", pady=(0, 10), padx=10)

        # 测试连接按钮
        self.test_btn = ctk.CTkButton(
            self.api_tab,
            text="🔍 测试连接",
            command=self._test_connection,
            height=34,
            fg_color="#8e44ad",
            hover_color="#7d3c98"
        )
        self.test_btn.pack(pady=15)

        # 测试状态
        self.test_status = ctk.CTkLabel(
            self.api_tab,
            text="",
            text_color="gray"
        )
        self.test_status.pack(pady=5)

        # ==================== 提示词设置标签页 ====================
        # 片段拆分提示词
        segment_label = ctk.CTkLabel(
            self.prompt_tab,
            text="片段拆分系统提示词：",
            font=ctk.CTkFont(weight="bold")
        )
        segment_label.pack(anchor="w", padx=10, pady=(10, 5))

        # 创建滚动文本框
        self.segment_prompt_text = ctk.CTkTextbox(
            self.prompt_tab,
            height=250,
            wrap="word"
        )
        self.segment_prompt_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 重置片段提示词按钮
        self.reset_segment_btn = ctk.CTkButton(
            self.prompt_tab,
            text="🔄 重置片段提示词",
            command=self._reset_segment_prompt,
            height=30,
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        self.reset_segment_btn.pack(anchor="w", padx=10, pady=(0, 15))

        # 摘要提示词
        summary_label = ctk.CTkLabel(
            self.prompt_tab,
            text="九宫格简述提示词模板：",
            font=ctk.CTkFont(weight="bold")
        )
        summary_label.pack(anchor="w", padx=10, pady=(0, 5))

        self.summary_prompt_text = ctk.CTkTextbox(
            self.prompt_tab,
            height=100,
            wrap="word"
        )
        self.summary_prompt_text.pack(fill="x", padx=10, pady=(0, 10))

        # 重置摘要提示词按钮
        self.reset_summary_btn = ctk.CTkButton(
            self.prompt_tab,
            text="🔄 重置摘要提示词",
            command=self._reset_summary_prompt,
            height=30,
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        self.reset_summary_btn.pack(anchor="w", padx=10, pady=(0, 10))

        # 提示信息
        prompt_hint = ctk.CTkLabel(
            self.prompt_tab,
            text="💡 摘要提示词模板中可使用 {max_length} 占位符表示最大字数限制",
            text_color="gray",
            font=ctk.CTkFont(size=11)
        )
        prompt_hint.pack(anchor="w", padx=10, pady=(0, 10))

        # 底部按钮（固定在窗口底部，不滚动）
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 15), padx=21)

        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 保存",
            command=self._save,
            height=34,
            fg_color="#27ae60",
            hover_color="#229954"
        )
        self.save_btn.pack(side="right", padx=6)

        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ 取消",
            command=self._cancel,
            height=34,
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        )
        self.cancel_btn.pack(side="right", padx=6)

    def _load_config(self):
        """加载配置"""
        api_settings = self.config_manager.get_api_settings()
        platform_id = api_settings.get("platform", "qwen")

        # 设置平台
        if platform_id in self.platform_ids:
            idx = self.platform_ids.index(platform_id)
            platform_name = list(self.config_manager.PLATFORMS.values())[idx]["name"]
            self.platform_var.set(platform_name)
            self._update_platform_hint(platform_id)

        # 设置API Key
        self.key_entry.insert(0, api_settings.get("api_key", ""))

        # 设置端点
        endpoint = api_settings.get("endpoint", "")
        if endpoint != self.config_manager.PLATFORMS.get(platform_id, {}).get("endpoint", ""):
            self.endpoint_entry.insert(0, endpoint)

        # 设置模型
        model = api_settings.get("model", "")
        if model:
            self.model_entry.insert(0, model)
        else:
            # 使用默认模型
            default_model = self.config_manager.PLATFORMS.get(platform_id, {}).get("default_model", "")
            if default_model:
                self.model_entry.insert(0, default_model)

        # 加载提示词配置
        prompt_settings = self.config_manager.get_prompt_settings()
        self.segment_prompt_text.insert("1.0", prompt_settings.get("segment_split_prompt", ""))
        self.summary_prompt_text.insert("1.0", prompt_settings.get("summary_prompt", ""))

    def _on_platform_change(self, platform_name: str):
        """平台变更"""
        # 找到对应的平台ID
        for pid, pinfo in self.config_manager.PLATFORMS.items():
            if pinfo["name"] == platform_name:
                self._update_platform_hint(pid)

                # 更新端点（如果是非自定义平台）
                default_endpoint = pinfo.get("endpoint", "")
                if pid != "custom" and default_endpoint:
                    self.endpoint_entry.delete(0, "end")
                    self.endpoint_entry.insert(0, default_endpoint)

                # 更新默认模型
                default_model = pinfo.get("default_model", "")
                if default_model:
                    self.model_entry.delete(0, "end")
                    self.model_entry.insert(0, default_model)
                break

    def _update_platform_hint(self, platform_id: str):
        """更新平台提示信息"""
        platform_info = self.config_manager.PLATFORMS.get(platform_id, {})
        hint = platform_info.get("key_hint", "")
        if hint:
            self.platform_hint.configure(text=f"💡 {hint}")
        else:
            self.platform_hint.configure(text="")

    def _toggle_key_visibility(self):
        """切换Key可见性"""
        if self.show_key_var.get():
            self.key_entry.configure(show="")
        else:
            self.key_entry.configure(show="*")

    def _reset_segment_prompt(self):
        """重置片段拆分提示词为默认值"""
        default_prompt = self.config_manager.DEFAULT_CONFIG["prompt_settings"]["segment_split_prompt"]
        self.segment_prompt_text.delete("1.0", "end")
        self.segment_prompt_text.insert("1.0", default_prompt)

    def _reset_summary_prompt(self):
        """重置摘要提示词为默认值"""
        default_prompt = self.config_manager.DEFAULT_CONFIG["prompt_settings"]["summary_prompt"]
        self.summary_prompt_text.delete("1.0", "end")
        self.summary_prompt_text.insert("1.0", default_prompt)

    def _test_connection(self):
        """测试连接"""
        self.test_status.configure(text="测试中...", text_color="orange")

        # 临时保存设置
        self._save_temp()

        # 测试
        from core.ai_engine import AIEngine
        engine = AIEngine(self.config_manager)
        success, message = engine.test_connection()

        if success:
            self.test_status.configure(text=f"✅ {message}", text_color="green")
        else:
            self.test_status.configure(text=f"❌ {message}", text_color="red")

    def _save_temp(self):
        """临时保存设置"""
        platform_name = self.platform_var.get()
        platform_id = "custom"
        for pid, pinfo in self.config_manager.PLATFORMS.items():
            if pinfo["name"] == platform_name:
                platform_id = pid
                break

        settings = {
            "platform": platform_id,
            "api_key": self.key_entry.get(),
            "endpoint": self.endpoint_entry.get() or self.config_manager.PLATFORMS.get(platform_id, {}).get("endpoint", ""),
            "model": self.model_entry.get(),
            "mode": self.config_manager.PLATFORMS.get(platform_id, {}).get("mode", "openai")
        }

        self.config_manager.set_api_settings(settings)

        # 保存提示词配置
        prompt_settings = {
            "segment_split_prompt": self.segment_prompt_text.get("1.0", "end-1c"),
            "summary_prompt": self.summary_prompt_text.get("1.0", "end-1c")
        }
        self.config_manager.set_prompt_settings(prompt_settings)

    def _save(self):
        """保存设置"""
        self._save_temp()
        self.result = True
        self.destroy()

    def _cancel(self):
        """取消"""
        self.result = False
        self.destroy()