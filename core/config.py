# -*- coding: utf-8 -*-
"""
配置管理模块
管理API设置、应用配置等
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG = {
        "api_settings": {
            "platform": "qwen",  # 默认使用通义千问
            "api_key": "",
            "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "model": "qwen-max",
            "mode": "openai"
        },
        "video_settings": {
            "min_duration": 5,
            "max_duration": 15,
            "default_duration": 10
        },
        "app_settings": {
            "theme": "dark-blue",
            "auto_save": True,
            "output_dir": ""
        },
        "prompt_settings": {
            "segment_split_prompt": """你是一个专业的视频分镜导演，擅长将故事拆分成5-15秒的视频片段提示词。

【核心任务】
将用户提供的视频描述或旁白拆分成多个独立的视频片段，每个片段5-15秒。

【重要规则】
1. 必须直接输出JSON数组，不要使用```json```代码块包裹
2. 不要输出任何解释性文字，只输出纯JSON
3. 确保输出完整的JSON数组，包括结尾的 ]

【输出格式】
必须输出JSON数组，每个元素包含：
- index: 片段序号（从1开始）
- duration: 预估时长（秒，5-15之间）
- narration: 该片段的旁白/对话文本（如果有）
- prompt: 视频生成的详细提示词
- references: 引用的素材名称列表（如人物名、场景名，用于后续匹配@[文件名]格式）

【提示词格式】（每个片段必须遵循）
镜头：【景别+运镜】 环境：在@图片N [场景描述] 角色分动：@人物N [外观] 正在 [动作] 细节：[微表情与情绪] 光影：[光源+质感+色调] 音效：[环境音+声响] 台词：["对白"]

【规则】
1. 每个片段必须能独立生成视频，同时保持故事连贯性
2. 如果提供了旁白文本，片段时长要匹配旁白的朗读时长（约每秒3-4个字）
3. 引用的素材使用@[文件名.扩展名]格式，如@[角色A.png]
4. 提示词要具体、可视化，避免抽象描述
5. 保持角色外观、场景的一致性

【示例输出】
[
  {
    "index": 1,
    "duration": 8,
    "narration": "",
    "prompt": "镜头：【中景推进】 环境：@[城市夜景.png] 霓虹闪烁的街道，雨后积水反射灯光 角色分动：@[主角.png] [黑色风衣] 正在 快步行走，衣角随风飘动 细节：[眉头紧锁，眼神坚定] 光影：[侧光，冷色调蓝紫光] 音效：[雨声+远处的车流声]",
    "references": ["主角.png", "城市夜景.png"]
  }
]
""",
            "summary_prompt": "你是一个文案编辑，请将以下视频分镜提示词简化为{max_length}字以内的剧情简述。\n只输出简述文字，不要任何额外说明。"
        }
    }

    # 支持的AI平台配置
    PLATFORMS = {
        "qwen": {
            "name": "通义千问",
            "icon": "🌐",
            "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "key_hint": "在阿里云百炼控制台获取 API Key",
            "key_link": "https://bailian.console.aliyun.com/",
            "default_model": "qwen-max",
            "mode": "openai"
        },
        "doubao": {
            "name": "豆包",
            "icon": "🫘",
            "endpoint": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            "key_hint": "在火山引擎控制台获取 API Key，模型填推理接入点 ID（ep-xxx）",
            "key_link": "https://console.volcengine.com/ark",
            "default_model": "doubao-seed-2-0-pro-260215",
            "mode": "openai"
        },
        "deepseek": {
            "name": "DeepSeek",
            "icon": "🔍",
            "endpoint": "https://api.deepseek.com/v1/chat/completions",
            "key_hint": "在 platform.deepseek.com 获取 API Key",
            "key_link": "https://platform.deepseek.com/",
            "default_model": "deepseek-chat",
            "mode": "openai"
        },
        "gemini": {
            "name": "Gemini",
            "icon": "♊",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "key_hint": "在 Google AI Studio 获取免费 API Key",
            "key_link": "https://aistudio.google.com/app/apikey",
            "default_model": "gemini-2.0-flash",
            "mode": "openai"
        },
        "openai": {
            "name": "OpenAI",
            "icon": "🤖",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "key_hint": "在 platform.openai.com 获取 API Key",
            "key_link": "https://platform.openai.com/api-keys",
            "default_model": "gpt-4o",
            "mode": "openai"
        },
        "kimi": {
            "name": "Kimi",
            "icon": "🌙",
            "endpoint": "https://api.moonshot.cn/v1/chat/completions",
            "key_hint": "在 platform.moonshot.cn 获取 API Key",
            "key_link": "https://platform.moonshot.cn/",
            "default_model": "moonshot-v1-128k",
            "mode": "openai"
        },
        "siliconflow": {
            "name": "硅基流动",
            "icon": "⚡",
            "endpoint": "https://api.siliconflow.cn/v1/chat/completions",
            "key_hint": "在 siliconflow.cn 注册获取免费额度",
            "key_link": "https://cloud.siliconflow.cn/",
            "default_model": "deepseek-ai/DeepSeek-V3",
            "mode": "openai"
        },
        "openrouter": {
            "name": "OpenRouter",
            "icon": "🔀",
            "endpoint": "https://openrouter.ai/api/v1/chat/completions",
            "key_hint": "统一接入 Claude、GPT、Gemini 等",
            "key_link": "https://openrouter.ai/keys",
            "default_model": "anthropic/claude-sonnet-4-5",
            "mode": "openai"
        },
        "zhipu": {
            "name": "智谱 AI",
            "icon": "🧠",
            "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "key_hint": "在 open.bigmodel.cn 获取 API Key",
            "key_link": "https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys",
            "default_model": "glm-4-plus",
            "mode": "openai"
        },
        "custom": {
            "name": "自定义",
            "icon": "🔧",
            "endpoint": "",
            "key_hint": "填写任何兼容 OpenAI 格式的 API 端点",
            "key_link": "",
            "default_model": "",
            "mode": "openai"
        }
    }

    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器"""
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认在用户目录下创建配置文件夹
            self.config_dir = Path.home() / ".video_segment_tool"

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置（处理新增配置项）
                merged = self.DEFAULT_CONFIG.copy()
                self._deep_merge(merged, config)
                return merged
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def _deep_merge(self, base: dict, update: dict):
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_api_settings(self) -> Dict[str, str]:
        """获取API设置"""
        return self.config.get("api_settings", self.DEFAULT_CONFIG["api_settings"])

    def set_api_settings(self, settings: Dict[str, str]):
        """设置API配置"""
        self.config["api_settings"] = settings
        self.save_config()

    def get_platform_info(self, platform_id: str) -> Dict[str, Any]:
        """获取平台信息"""
        return self.PLATFORMS.get(platform_id, self.PLATFORMS["custom"])

    def get_video_settings(self) -> Dict[str, int]:
        """获取视频设置"""
        return self.config.get("video_settings", self.DEFAULT_CONFIG["video_settings"])

    def get_app_settings(self) -> Dict[str, Any]:
        """获取应用设置"""
        return self.config.get("app_settings", self.DEFAULT_CONFIG["app_settings"])

    def set_output_dir(self, path: str):
        """设置输出目录"""
        self.config["app_settings"]["output_dir"] = path
        self.save_config()

    def get_output_dir(self) -> str:
        """获取输出目录"""
        return self.config.get("app_settings", {}).get("output_dir", "")

    def get_prompt_settings(self) -> Dict[str, str]:
        """获取提示词设置"""
        return self.config.get("prompt_settings", self.DEFAULT_CONFIG["prompt_settings"])

    def set_prompt_settings(self, settings: Dict[str, str]):
        """设置提示词配置"""
        self.config["prompt_settings"] = settings
        self.save_config()