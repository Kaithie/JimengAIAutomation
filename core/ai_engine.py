# -*- coding: utf-8 -*-
"""
AI引擎模块
处理与AI API的交互，包括片段拆分、提示词生成等
"""

import json
import re
import requests
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Segment:
    """视频片段数据类"""
    index: int
    prompt: str
    duration: float
    references: List[str]  # 引用的素材文件名
    video_path: Optional[str] = None
    narration: str = ""  # 旁白文本（如果有）


class AIEngine:
    """AI引擎，处理API调用和内容生成"""


    def __init__(self, config_manager):
        """
        初始化AI引擎

        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.timeout = 120  # API超时时间（秒）

    def _build_request(self, messages: List[Dict], stream: bool = False) -> Tuple[str, dict, dict]:
        """
        构建API请求

        Args:
            messages: 消息列表
            stream: 是否流式输出

        Returns:
            (url, headers, body)
        """
        api_settings = self.config.get_api_settings()
        endpoint = api_settings.get("endpoint", "")
        api_key = api_settings.get("api_key", "")
        model = api_settings.get("model", "qwen-max")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 16384  # 增加token限制，确保完整输出
        }

        if stream:
            body["stream"] = True

        return endpoint, headers, body

    def call_api(self, system_prompt: str, user_content: str,
                 on_chunk: Optional[callable] = None) -> Tuple[bool, str]:
        """
        调用AI API

        Args:
            system_prompt: 系统提示词
            user_content: 用户输入内容
            on_chunk: 流式回调函数（可选）

        Returns:
            (success, response_text)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            url, headers, body = self._build_request(messages, stream=on_chunk is not None)

            if on_chunk:
                # 流式请求 - 使用更健壮的处理方式
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    stream=True,
                    timeout=(30, 300)  # (连接超时, 读取超时)
                )
                response.raise_for_status()

                full_content = ""
                buffer = ""  # 缓冲区用于处理不完整的行

                # 使用 iter_content 逐块读取，更健壮
                for chunk in response.iter_content(chunk_size=None):
                    if not chunk:
                        continue
                    try:
                        chunk_text = chunk.decode('utf-8')
                    except UnicodeDecodeError:
                        continue

                    buffer += chunk_text

                    # 按行分割处理
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()

                        if not line:
                            continue

                        # 处理 SSE 格式
                        if line.startswith("data: "):
                            data = line[6:].strip()
                            if data == "[DONE]":
                                return True, full_content
                            try:
                                chunk_data = json.loads(data)

                                # 兼容 OpenAI 格式
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")

                                # 兼容 Gemini 格式
                                if not content:
                                    candidates = chunk_data.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        if parts:
                                            content = parts[0].get("text", "")

                                if content:
                                    full_content += content
                                    if on_chunk:
                                        on_chunk(content)
                            except json.JSONDecodeError as e:
                                # 记录解析错误但继续处理
                                print(f"[DEBUG] JSON解析错误: {e}, 数据: {data[:100]}")
                                continue

                        # 处理非标准格式（有些API不使用 data: 前缀）
                        elif line.startswith("{"):
                            try:
                                chunk_data = json.loads(line)
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                                    if on_chunk:
                                        on_chunk(content)
                            except json.JSONDecodeError:
                                continue

                # 处理缓冲区剩余内容
                if buffer.strip():
                    if buffer.startswith("data: "):
                        data = buffer[6:].strip()
                        if data != "[DONE]":
                            try:
                                chunk_data = json.loads(data)
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                            except:
                                pass

                return True, full_content
            else:
                # 普通请求
                response = requests.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=(30, 180)  # (连接超时, 读取超时)
                )

                # 打印调试信息
                if not response.ok:
                    error_text = response.text[:500]
                    print(f"[DEBUG] API错误响应: HTTP {response.status_code}, {error_text}")

                response.raise_for_status()
                result = response.json()

                # 提取响应内容
                choices = result.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    return True, content

                # 检查是否是 Gemini 格式
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        content = parts[0].get("text", "")
                        if content:
                            return True, content

                return False, "API返回格式异常"

        except requests.exceptions.Timeout:
            return False, "API请求超时，请检查网络连接或稍后重试"
        except requests.exceptions.ConnectionError as e:
            return False, f"网络连接错误: {str(e)[:100]}"
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            # 尝试获取更详细的错误信息
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    if 'error' in error_detail:
                        error_msg = error_detail['error'].get('message', str(e))
                except:
                    error_msg = e.response.text[:200] if e.response.text else str(e)
            return False, f"API请求失败: {error_msg}"
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"未知错误: {str(e)}"

    def test_connection(self) -> Tuple[bool, str]:
        """
        测试API连接

        Returns:
            (success, message)
        """
        success, response = self.call_api(
            "你是一个助手，请简短回复。",
            "请回复：连接成功"
        )
        if success:
            return True, f"连接成功: {response[:50]}"
        return False, response

    def split_into_segments(self, description: str, materials: Dict[str, List[Dict]],
                            on_progress: Optional[callable] = None) -> Tuple[bool, List[Segment]]:
        """
        将描述拆分成视频片段

        Args:
            description: 视频描述或旁白
            materials: 素材字典 {"characters": [...], "scenes": [...], "voices": [...]}
            on_progress: 进度回调

        Returns:
            (success, segments)
        """
        # 构建用户消息
        user_message = self._build_user_message(description, materials)

        # 调用API
        if on_progress:
            on_progress("正在调用AI分析内容...")

        # 从配置中获取片段拆分提示词
        prompt_settings = self.config.get_prompt_settings()
        segment_prompt = prompt_settings.get("segment_split_prompt", "")

        success, response = self.call_api(segment_prompt, user_message)

        if not success:
            print(f"[DEBUG] API调用失败: {response}")
            return False, []

        if on_progress:
            on_progress("正在解析AI返回结果...")

        # 打印原始响应用于调试
        print(f"[DEBUG] API响应长度: {len(response)} 字符")
        if len(response) < 500:
            print(f"[DEBUG] API响应内容: {response}")
        else:
            print(f"[DEBUG] API响应前500字符: {response[:500]}")

        # 解析结果
        segments = self._parse_segments(response, materials)

        if not segments:
            print("[DEBUG] 解析失败，未能提取到片段")
            # 尝试返回一个提示信息
            return False, []

        print(f"[DEBUG] 成功解析 {len(segments)} 个片段")
        return True, segments

    def _build_user_message(self, description: str, materials: Dict[str, List[Dict]]) -> str:
        """
        构建用户消息

        Args:
            description: 视频描述
            materials: 素材信息

        Returns:
            用户消息字符串
        """
        message_parts = []

        # 添加素材信息
        characters = materials.get("characters", [])
        scenes = materials.get("scenes", [])
        voices = materials.get("voices", [])

        if characters:
            char_info = "\n【已上传人物素材】\n"
            for i, char in enumerate(characters, 1):
                char_info += f"- @人物{i} ({char.get('name', '未命名')})：{char.get('desc', '')}\n"
            message_parts.append(char_info)

        if scenes:
            scene_info = "\n【已上传场景素材】\n"
            for i, scene in enumerate(scenes, 1):
                scene_info += f"- @图片{i} ({scene.get('name', '未命名')})：{scene.get('desc', '')}\n"
            message_parts.append(scene_info)

        if voices:
            voice_info = "\n【已上传声线素材】\n"
            for i, voice in enumerate(voices, 1):
                voice_info += f"- 声线{i} ({voice.get('name', '未命名')})\n"
            message_parts.append(voice_info)

        # 添加描述
        message_parts.append(f"\n【视频描述/旁白】\n{description}")

        return "\n".join(message_parts)

    def _extract_json_array(self, text: str) -> Optional[str]:
        """
        从文本中提取JSON数组，使用括号匹配算法

        Args:
            text: 可能包含JSON数组的文本

        Returns:
            提取到的JSON数组字符串，或None
        """
        # 找到所有可能的数组起始位置
        for i, char in enumerate(text):
            if char == '[':
                # 尝试从这个位置开始匹配完整的JSON数组
                depth = 0
                in_string = False
                escape_next = False

                for j in range(i, len(text)):
                    c = text[j]

                    if escape_next:
                        escape_next = False
                        continue

                    if c == '\\':
                        escape_next = True
                        continue

                    if c == '"' and not escape_next:
                        in_string = not in_string
                        continue

                    if not in_string:
                        if c == '[':
                            depth += 1
                        elif c == ']':
                            depth -= 1
                            if depth == 0:
                                # 找到匹配的结束括号
                                candidate = text[i:j+1]
                                # 验证是否是有效的JSON数组
                                try:
                                    data = json.loads(candidate)
                                    if isinstance(data, list):
                                        return candidate
                                except:
                                    pass
                                break

        return None

    def _parse_segments(self, response: str, materials: Dict[str, List[Dict]]) -> List[Segment]:
        """
        解析AI返回的片段

        Args:
            response: API响应
            materials: 素材信息

        Returns:
            片段列表
        """
        segments = []

        # 尝试提取JSON
        try:
            # 尝试直接解析
            data = json.loads(response)
        except json.JSONDecodeError:
            # 尝试从markdown代码块中提取
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if json_match:
                try:
                    data = json.loads(json_match.group(1).strip())
                except:
                    # 使用括号匹配算法提取数组
                    array_str = self._extract_json_array(response)
                    if array_str:
                        try:
                            data = json.loads(array_str)
                        except Exception as e:
                            print(f"[DEBUG] JSON解析失败: {e}")
                            print(f"[DEBUG] 提取的数组内容前200字符: {array_str[:200]}")
                            return segments
                    else:
                        print("[DEBUG] 未找到有效的JSON数组")
                        return segments
            else:
                # 使用括号匹配算法提取数组
                array_str = self._extract_json_array(response)
                if array_str:
                    try:
                        data = json.loads(array_str)
                    except Exception as e:
                        print(f"[DEBUG] 数组解析失败: {e}")
                        print(f"[DEBUG] 提取的数组内容前200字符: {array_str[:200]}")
                        return segments
                else:
                    print("[DEBUG] 响应中未找到JSON数组")
                    return segments

        # 确保是列表
        if isinstance(data, dict):
            # 尝试多种可能的键名
            for key in ["segments", "scenes", "shots", "items", "data"]:
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
            else:
                # 如果没有找到列表，可能单个对象
                if "prompt" in data or "index" in data:
                    data = [data]
                else:
                    print(f"[DEBUG] 无法从字典中提取片段，键: {list(data.keys())}")
                    return segments

        if not isinstance(data, list):
            print(f"[DEBUG] 数据不是列表类型: {type(data)}")
            return segments

        # 解析每个片段
        for i, item in enumerate(data, 1):
            if not isinstance(item, dict):
                print(f"[DEBUG] 跳过非字典项: {type(item)}")
                continue

            # 提取字段，支持多种键名
            index = item.get("index") or item.get("id") or item.get("序号") or i
            prompt = item.get("prompt") or item.get("提示词") or item.get("description") or item.get("描述") or ""
            duration = item.get("duration") or item.get("时长") or item.get("time") or 10
            references = item.get("references") or item.get("引用") or item.get("refs") or []
            narration = item.get("narration") or item.get("旁白") or item.get("dialogue") or item.get("台词") or ""

            try:
                segment = Segment(
                    index=int(index) if index else i,
                    prompt=str(prompt),
                    duration=float(duration) if duration else 10.0,
                    references=list(references) if references else [],
                    narration=str(narration) if narration else ""
                )

                # 处理引用，替换为实际文件名
                segment.prompt = self._resolve_references(segment.prompt, materials)

                # 从 prompt 中提取实际的 @[文件名] 引用，更新 references 列表
                segment.references = self._extract_references_from_prompt(segment.prompt)

                segments.append(segment)
            except Exception as e:
                print(f"[DEBUG] 创建片段失败: {e}, 数据: {item}")
                continue

        return segments

    def _resolve_references(self, prompt: str, materials: Dict[str, List[Dict]]) -> str:
        """
        解析引用，将@人物N等替换为实际文件名

        Args:
            prompt: 原始提示词
            materials: 素材信息

        Returns:
            处理后的提示词
        """
        result = prompt

        # 替换人物引用
        characters = materials.get("characters", [])
        for i, char in enumerate(characters, 1):
            pattern = f"@人物{i}"
            filename = char.get("filename", "")
            if filename:
                result = result.replace(pattern, f"@[{filename}]")

        # 替换场景引用
        scenes = materials.get("scenes", [])
        for i, scene in enumerate(scenes, 1):
            pattern = f"@图片{i}"
            filename = scene.get("filename", "")
            if filename:
                result = result.replace(pattern, f"@[{filename}]")

        return result

    def _extract_references_from_prompt(self, prompt: str) -> List[str]:
        """
        从 prompt 中提取 @[文件名] 格式的引用

        Args:
            prompt: 包含引用的提示词

        Returns:
            引用的文件名列表
        """
        import re
        # 匹配 @[文件名] 格式的引用
        pattern = r'@\[([^\]]+)\]'
        matches = re.findall(pattern, prompt)
        return list(set(matches))  # 去重

    def simplify_prompt(self, prompt: str, max_length: int = 30) -> Tuple[bool, str]:
        """
        简化提示词为剧情简述

        Args:
            prompt: 原始提示词
            max_length: 最大字数

        Returns:
            (success, simplified_text)
        """
        # 从配置中获取摘要提示词模板
        prompt_settings = self.config.get_prompt_settings()
        summary_prompt_template = prompt_settings.get("summary_prompt", "你是一个文案编辑，请将以下视频分镜提示词简化为{max_length}字以内的剧情简述。\n只输出简述文字，不要任何额外说明。")
        system_prompt = summary_prompt_template.format(max_length=max_length)

        success, response = self.call_api(system_prompt, prompt)
        return success, response[:max_length] if success else ""