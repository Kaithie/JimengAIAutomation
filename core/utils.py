# -*- coding: utf-8 -*-
"""
工具模块
包含文件操作、视频处理等工具函数
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class FileUtils:
    """文件操作工具类"""

    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}

    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def ensure_dir(dir_path: str) -> Path:
        """确保目录存在"""
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """复制文件"""
        try:
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"复制文件失败: {e}")
            return False

    @staticmethod
    def copy_files_to_segment(src_files: List[str], dst_dir: str) -> List[str]:
        """
        复制多个文件到目标目录，保持原文件名

        Args:
            src_files: 源文件列表
            dst_dir: 目标目录

        Returns:
            复制成功的文件路径列表
        """
        FileUtils.ensure_dir(dst_dir)
        copied = []
        for src in src_files:
            if os.path.exists(src):
                dst = os.path.join(dst_dir, os.path.basename(src))
                if FileUtils.copy_file(src, dst):
                    copied.append(dst)
        return copied

    @staticmethod
    def get_unique_filename(directory: str, filename: str) -> str:
        """获取不重复的文件名"""
        base, ext = os.path.splitext(filename)
        counter = 1
        result = filename
        while os.path.exists(os.path.join(directory, result)):
            result = f"{base}_{counter}{ext}"
            counter += 1
        return result

    @staticmethod
    def is_image_file(filepath: str) -> bool:
        """检查是否为图片文件"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in FileUtils.SUPPORTED_IMAGE_FORMATS

    @staticmethod
    def is_video_file(filepath: str) -> bool:
        """检查是否为视频文件"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in FileUtils.SUPPORTED_VIDEO_FORMATS

    @staticmethod
    def is_audio_file(filepath: str) -> bool:
        """检查是否为音频文件"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in FileUtils.SUPPORTED_AUDIO_FORMATS

    @staticmethod
    def extract_references_from_prompt(prompt: str) -> List[str]:
        """
        从提示词中提取引用的文件名

        Args:
            prompt: 提示词文本

        Returns:
            引用的文件名列表
        """
        import re
        # 匹配@[文件名.扩展名]格式
        pattern = r'@\[([^\]]+\.[a-zA-Z0-9]+)\]'
        matches = re.findall(pattern, prompt)
        return list(set(matches))  # 去重


class VideoUtils:
    """视频处理工具类"""

    @staticmethod
    def get_video_duration(video_path: str) -> float:
        """
        获取视频时长（秒）

        Args:
            video_path: 视频文件路径

        Returns:
            视频时长（秒）
        """
        try:
            from moviepy import VideoFileClip
            with VideoFileClip(video_path) as clip:
                return clip.duration
        except Exception as e:
            print(f"获取视频时长失败: {e}")
            return 0.0

    @staticmethod
    def extract_frames(video_path: str, num_frames: int = 9,
                       output_dir: Optional[str] = None) -> List[str]:
        """
        从视频中均匀提取帧，必须包含第一帧和最后一帧
        使用 ffmpeg 精确提取，确保时间点准确

        Args:
            video_path: 视频文件路径
            num_frames: 要提取的帧数（默认9帧）
            output_dir: 输出目录

        Returns:
            提取的帧图片路径列表
        """
        import subprocess

        try:
            if output_dir is None:
                output_dir = os.path.dirname(video_path)

            FileUtils.ensure_dir(output_dir)

            # 获取视频时长
            duration = VideoUtils.get_video_duration(video_path)
            if duration <= 0:
                print(f"无法获取视频时长: {video_path}")
                return []

            print(f"[DEBUG] 视频时长: {duration}秒, 提取{num_frames}帧")

            frames = []

            for i in range(num_frames):
                # 第一帧: t=0, 最后一帧: t接近duration
                if i == 0:
                    t = 0
                elif i == num_frames - 1:
                    # 最后一帧：使用 duration - 微小偏移
                    t = max(0, duration - 0.1)
                else:
                    t = duration * i / (num_frames - 1)

                frame_path = os.path.join(output_dir, f"frame_{i+1:02d}.png")

                # 使用 ffmpeg 精确提取帧
                # -ss: 跳转到指定时间点（放在 -i 前面可以快速定位）
                # -i: 输入文件
                # -vframes 1: 只提取一帧
                # -y: 覆盖已存在的文件
                cmd = [
                    'ffmpeg',
                    '-ss', str(t),
                    '-i', video_path,
                    '-vframes', '1',
                    '-y',
                    frame_path
                ]

                print(f"[DEBUG] 第{i+1}帧: 时间点 {t:.3f}秒 ({t/duration*100:.1f}%)")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',  # 忽略无法解码的字符
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                if os.path.exists(frame_path):
                    frames.append(frame_path)
                else:
                    print(f"[WARN] ffmpeg 提取第{i+1}帧失败: {result.stderr}")

            print(f"[DEBUG] 成功提取 {len(frames)}/{num_frames} 帧")
            return frames

        except FileNotFoundError:
            print("ffmpeg 未安装，请先安装 ffmpeg 并添加到 PATH")
            return []
        except Exception as e:
            print(f"提取帧失败: {e}")
            return []

    @staticmethod
    def create_nine_grid(image_paths: List[str], output_path: str,
                         text: str = "", text_position: str = "bottom") -> bool:
        """
        创建九宫格图片

        Args:
            image_paths: 9张图片路径列表
            output_path: 输出路径
            text: 要添加的文字
            text_position: 文字位置 (top/bottom)

        Returns:
            是否成功
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            if len(image_paths) < 9:
                print(f"图片数量不足9张: {len(image_paths)}")
                return False

            # 计算单个图片大小
            first_img = Image.open(image_paths[0])
            img_w, img_h = first_img.size
            aspect_ratio = img_w / img_h

            # 设置九宫格参数
            grid_size = 3
            padding = 10
            text_height = 60 if text else 0

            # 计算输出图片尺寸
            cell_width = 200
            cell_height = int(cell_width / aspect_ratio)
            total_width = cell_width * grid_size + padding * (grid_size + 1)
            total_height = cell_height * grid_size + padding * (grid_size + 1) + text_height

            # 创建新图片
            result = Image.new('RGB', (total_width, total_height), 'white')
            draw = ImageDraw.Draw(result)

            # 粘贴图片
            for i, img_path in enumerate(image_paths[:9]):
                row = i // grid_size
                col = i % grid_size
                img = Image.open(img_path)
                img = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)

                x = padding + col * (cell_width + padding)
                y = padding + row * (cell_height + padding)

                result.paste(img, (x, y))

            # 添加文字
            if text:
                try:
                    # 尝试使用系统中文字体
                    font = ImageFont.truetype("msyh.ttc", 16)  # 微软雅黑
                except:
                    font = ImageFont.load_default()

                # 计算文字位置
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = (total_width - text_width) // 2

                if text_position == "top":
                    text_y = padding
                else:
                    text_y = total_height - text_height + 20

                draw.text((text_x, text_y), text, fill='black', font=font)

            # 保存结果
            result.save(output_path)
            return True

        except Exception as e:
            print(f"创建九宫格失败: {e}")
            return False


class ProjectManager:
    """项目管理器"""

    def __init__(self, base_dir: str):
        """
        初始化项目管理器

        Args:
            base_dir: 项目基础目录
        """
        self.base_dir = Path(base_dir)
        self.current_project: Optional[str] = None
        self.project_dir: Optional[Path] = None

    def create_project(self, name: str) -> Path:
        """
        创建新项目

        Args:
            name: 项目名称

        Returns:
            项目目录路径
        """
        # 生成唯一项目名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"{name}_{timestamp}"
        self.project_dir = self.base_dir / project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # 创建统一的 assets 目录，所有素材和生成文件都放在这里
        # 人物图片、场景图片、声线文件、九宫格图片全部放在一起
        # 方便后续对接即梦网站生成视频时引用文件
        (self.project_dir / "assets").mkdir(exist_ok=True)

        # 片段目录（存放片段视频）
        (self.project_dir / "segments").mkdir(exist_ok=True)

        # 输出目录
        (self.project_dir / "output").mkdir(exist_ok=True)

        self.current_project = project_name
        return self.project_dir

    def get_segment_dir(self, segment_index: int) -> Path:
        """获取片段目录"""
        if self.project_dir is None:
            raise ValueError("未创建项目")
        segment_dir = self.project_dir / "segments" / f"segment_{segment_index:03d}"
        segment_dir.mkdir(exist_ok=True)
        return segment_dir

    def get_assets_dir(self) -> Path:
        """获取 assets 目录（统一存放素材和生成文件）"""
        if self.project_dir is None:
            raise ValueError("未创建项目")
        return self.project_dir / "assets"

    def get_material_dir(self, material_type: str) -> Path:
        """获取素材目录（统一返回 assets 目录）"""
        if self.project_dir is None:
            raise ValueError("未创建项目")
        return self.project_dir / "assets"

    def get_grids_dir(self) -> Path:
        """获取九宫格图片目录（统一返回 assets 目录）"""
        if self.project_dir is None:
            raise ValueError("未创建项目")
        return self.project_dir / "assets"

    def copy_material_to_assets(self, src_path: str, material_type: str = None) -> str:
        """
        复制素材到 assets 目录

        Args:
            src_path: 源文件路径
            material_type: 素材类型（已忽略，统一放到 assets 目录）

        Returns:
            复制后的文件路径
        """
        if self.project_dir is None:
            raise ValueError("未创建项目")

        dst_dir = self.get_assets_dir()
        filename = os.path.basename(src_path)
        # 获取不重复的文件名
        unique_name = FileUtils.get_unique_filename(str(dst_dir), filename)
        dst_path = dst_dir / unique_name

        shutil.copy2(src_path, dst_path)
        return str(dst_path)

    def resolve_reference(self, ref_path: str) -> str:
        """
        解析引用路径，返回绝对路径

        Args:
            ref_path: 引用路径（文件名，如 "grid_001.png" 或 "xxx.png"）

        Returns:
            绝对路径
        """
        if self.project_dir is None:
            raise ValueError("未创建项目")

        # 如果已经是绝对路径，直接返回
        if os.path.isabs(ref_path):
            return ref_path

        # 在 assets 目录中查找
        full_path = self.project_dir / "assets" / ref_path
        if full_path.exists():
            return str(full_path)

        return str(full_path)  # 返回路径即使不存在

    def save_project_info(self, info: Dict):
        """保存项目信息"""
        if self.project_dir is None:
            return
        import json
        info_path = self.project_dir / "project_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

    def save_materials(self, materials: Dict):
        """
        保存素材元数据

        Args:
            materials: 素材字典 {"characters": [...], "scenes": [...], "voices": [...]}
        """
        if self.project_dir is None:
            raise ValueError("未创建项目")
        import json
        materials_path = self.project_dir / "materials_data.json"
        with open(materials_path, 'w', encoding='utf-8') as f:
            json.dump(materials, f, ensure_ascii=False, indent=2)
        return str(materials_path)

    def load_materials(self) -> Optional[Dict]:
        """
        加载素材元数据

        Returns:
            素材字典，如果文件不存在则返回 None
        """
        if self.project_dir is None:
            return None
        import json
        materials_path = self.project_dir / "materials_data.json"
        if materials_path.exists():
            with open(materials_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_description(self, description: str):
        """
        保存视频描述/旁白文本

        Args:
            description: 视频描述或旁白文本
        """
        if self.project_dir is None:
            raise ValueError("未创建项目")
        description_path = self.project_dir / "description.txt"
        with open(description_path, 'w', encoding='utf-8') as f:
            f.write(description)
        return str(description_path)

    def load_description(self) -> Optional[str]:
        """
        加载视频描述/旁白文本

        Returns:
            描述文本，如果文件不存在则返回 None
        """
        if self.project_dir is None:
            return None
        description_path = self.project_dir / "description.txt"
        if description_path.exists():
            with open(description_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def save_segments(self, segments: List[Dict]):
        """
        保存片段数据到文件

        Args:
            segments: 片段数据列表（已转换为字典格式）
        """
        if self.project_dir is None:
            raise ValueError("未创建项目")
        import json
        segments_path = self.project_dir / "segments_data.json"
        with open(segments_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        return str(segments_path)

    def load_segments(self) -> Optional[List[Dict]]:
        """
        加载片段数据

        Returns:
            片段数据列表，如果文件不存在则返回 None
        """
        if self.project_dir is None:
            return None
        segments_path = self.project_dir / "segments_data.json"
        if segments_path.exists():
            import json
            with open(segments_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def load_project_info(self) -> Optional[Dict]:
        """加载项目信息"""
        if self.project_dir is None:
            return None
        info_path = self.project_dir / "project_info.json"
        if info_path.exists():
            import json
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def load_project(self, project_path: str) -> bool:
        """
        加载已有项目

        Args:
            project_path: 项目目录路径

        Returns:
            是否成功加载
        """
        path = Path(project_path)
        if not path.exists():
            return False

        # 检查是否是有效的项目目录（包含必要的子目录）
        if not (path / "segments").exists():
            return False

        self.project_dir = path
        self.current_project = path.name

        # 确保新目录结构存在（兼容旧项目）
        (path / "assets").mkdir(exist_ok=True)

        return True

    def list_projects(self, base_dir: str) -> List[Dict]:
        """
        列出目录下的所有项目

        Args:
            base_dir: 基础目录

        Returns:
            项目列表，每个项目包含 name, path, create_time 等信息
        """
        base_path = Path(base_dir)
        if not base_path.exists():
            return []

        projects = []
        for item in base_path.iterdir():
            if item.is_dir() and (item / "segments").exists():
                # 这是一个有效的项目目录
                project_info = {
                    "name": item.name,
                    "path": str(item),
                    "create_time": datetime.fromtimestamp(item.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                }

                # 尝试加载项目信息
                info_path = item / "project_info.json"
                if info_path.exists():
                    try:
                        import json
                        with open(info_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                            project_info["description"] = info.get("description", "")
                    except:
                        pass

                projects.append(project_info)

        # 按创建时间倒序排列
        projects.sort(key=lambda x: x["create_time"], reverse=True)
        return projects