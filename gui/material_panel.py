# -*- coding: utf-8 -*-
"""
素材面板组件
管理人物图片、场景图片、声线等素材
"""

import customtkinter as ctk
from tkinter import filedialog
from typing import List, Dict, Optional, Callable
from pathlib import Path
import os


class MaterialPanel(ctk.CTkFrame):
    """素材面板"""

    MAX_CHARACTERS = 5  # 最多5个人物

    def __init__(self, master, on_material_change: Callable = None, get_project_dir: Callable = None):
        super().__init__(
            master,
            width=300,
            fg_color=["#ffffff", "#1e1e1e"],
            border_width=1,
            border_color=["#e2e8f0", "#333333"]
        )

        self.on_material_change = on_material_change
        self.get_project_dir = get_project_dir  # 获取项目目录的回调

        self.materials = {
            "characters": [],
            "scenes": [],
            "voices": []
        }

        self._create_ui()

    def _create_ui(self):
        """创建UI"""
        self.pack_propagate(False)  # 固定宽度

        # 标题
        title = ctk.CTkLabel(
            self,
            text="🎨 素材管理",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=["#2d3748", "#e2e8f0"]
        )
        title.pack(pady=12)

        # Tab按钮（分段控件样式）
        self.tab_frame = ctk.CTkFrame(self, fg_color=["#f5f7fa", "#2d3748"], corner_radius=8)
        self.tab_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.current_tab = ctk.StringVar(value="characters")

        tabs = [
            ("👤 人物", "characters"),
            ("🏞️ 场景", "scenes"),
            ("🎤 声线", "voices")
        ]

        for i, (tab_name, tab_id) in enumerate(tabs):
            btn = ctk.CTkButton(
                self.tab_frame,
                text=tab_name,
                width=80,
                height=32,
                fg_color="transparent" if self.current_tab.get() != tab_id else ["#3b7de8", "#3b7de8"],
                hover_color=["#cbd5e0", "#4a5568"],
                text_color=["#2d3748", "#e2e8f0"] if self.current_tab.get() != tab_id else "white",
                font=ctk.CTkFont(size=12),
                command=lambda t=tab_id: self._on_tab_click(t)
            )
            btn.pack(side="left", padx=2, pady=2)
            # 保存按钮引用以便切换时更新样式
            if not hasattr(self, 'tab_buttons'):
                self.tab_buttons = {}
            self.tab_buttons[tab_id] = btn

        # 内容区域
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=["#ffffff", "#2a2a2a"],
            scrollbar_button_color=["#e0e0e0", "#404040"],
            scrollbar_button_hover_color=["#bdbdbd", "#505050"]
        )
        self.content_frame.pack(fill="both", expand=True, padx=2, pady=5)

        # 添加按钮
        self.add_btn = ctk.CTkButton(
            self,
            text="➕ 添加素材",
            command=self._add_material,
            height=34,
            fg_color="#27ae60",
            hover_color="#229954"
        )
        self.add_btn.pack(pady=10, padx=10)

        # 显示人物面板
        self._switch_tab()

    def _on_tab_click(self, tab_id: str):
        """标签点击处理"""
        # 切换前保存当前输入框的值
        self._save_current_inputs()
        self.current_tab.set(tab_id)
        # 更新按钮样式
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=["#3b7de8", "#3b7de8"],
                    text_color="white"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=["#2d3748", "#e2e8f0"]
                )
        self._switch_tab()

    def _save_current_inputs(self):
        """保存当前页签所有输入框的值到数据中"""
        tab_id = self.current_tab.get()
        materials = self.materials.get(tab_id, [])

        # 遍历当前内容框中的所有素材项
        for widget in self.content_frame.winfo_children():
            if widget.winfo_class() == "CTkFrame":
                # 找到素材项中的输入框
                entries = widget.winfo_children()
                for item_widget in entries:
                    if item_widget.winfo_class() == "CTkFrame":
                        # 这是信息框，包含名称和描述输入框
                        info_entries = item_widget.winfo_children()
                        if len(info_entries) >= 2:
                            # 第一个可能是名称，第二个是描述
                            for i, entry in enumerate(info_entries):
                                if entry.winfo_class() == "CTkEntry":
                                    value = entry.get()
                                    # 通过索引找到对应的素材
                                    # 由于无法直接获取索引，这里需要另一种方式
                                    pass

        # 更可靠的方法：直接重新遍历内容框，按顺序保存
        items = []
        for widget in self.content_frame.winfo_children():
            if widget.winfo_class() == "CTkFrame":
                # 找到素材项中的所有子组件
                for child in widget.winfo_children():
                    if child.winfo_class() == "CTkFrame":
                        # 这是信息框
                        entries = [e for e in child.winfo_children() if e.winfo_class() == "CTkEntry"]
                        if len(entries) >= 2:
                            name_val = entries[0].get()
                            desc_val = entries[1].get()
                            items.append((name_val, desc_val))

        # 更新数据
        for i, (name_val, desc_val) in enumerate(items):
            if i < len(materials):
                materials[i]["name"] = name_val
                materials[i]["desc"] = desc_val

    def _switch_tab(self):
        """切换标签页"""
        # 清除内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        tab_id = self.current_tab.get()

        # 检查数量限制
        if tab_id == "characters":
            current_count = len(self.materials["characters"])
            if current_count >= self.MAX_CHARACTERS:
                self.add_btn.configure(state="disabled", text=f"已达上限({self.MAX_CHARACTERS}个)")
            else:
                self.add_btn.configure(state="normal", text=f"➕ 添加人物 ({current_count}/{self.MAX_CHARACTERS})")
        else:
            self.add_btn.configure(state="normal", text="➕ 添加素材")

        # 显示素材列表
        self._show_materials(tab_id)

    def _show_materials(self, material_type: str):
        """显示素材列表"""
        materials = self.materials.get(material_type, [])

        if not materials:
            empty_label = ctk.CTkLabel(
                self.content_frame,
                text=f"暂无{self._get_type_name(material_type)}素材",
                text_color="gray"
            )
            empty_label.pack(pady=20)
            return

        for i, material in enumerate(materials):
            self._create_material_item(material_type, i, material)

    def _create_material_item(self, material_type: str, index: int, material: Dict):
        """创建素材项"""
        item_frame = ctk.CTkFrame(
            self.content_frame,
            corner_radius=8,
            border_width=1,
            border_color=["#e2e8f0", "#3a3a3a"],
            fg_color=["#ffffff", "#2a2a2a"]
        )
        item_frame.pack(fill="x", pady=4, padx=4)

        # 添加悬浮效果
        original_color = item_frame.cget("fg_color")
        hover_color = ["#f7fafc", "#333333"]

        def on_enter(event):
            item_frame.configure(
                fg_color=hover_color,
                border_color=["#cbd5e0", "#4a5568"]
            )

        def on_leave(event):
            item_frame.configure(
                fg_color=original_color,
                border_color=["#e2e8f0", "#3a3a3a"]
            )

        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)

        # 缩略图（如果是图片）
        if material_type in ["characters", "scenes"]:
            if material.get("path") and os.path.exists(material["path"]):
                try:
                    # 加载缩略图
                    from PIL import Image, ImageTk
                    img = Image.open(material["path"])
                    img.thumbnail((60, 60))
                    photo = ctk.CTkImage(img, size=(60, 60))

                    img_label = ctk.CTkLabel(item_frame, image=photo, text="")
                    img_label.pack(side="left", padx=5, pady=5)
                except:
                    pass

        # 信息
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=5)

        # 名称
        name_entry = ctk.CTkEntry(
            info_frame,
            placeholder_text="名称",
            width=100
        )
        name_entry.pack(anchor="w")
        name_entry.insert(0, material.get("name", ""))
        name_entry.bind("<FocusOut>", lambda e, t=material_type, i=index: self._update_name(t, i, name_entry.get()))

        # 描述
        desc_entry = ctk.CTkEntry(
            info_frame,
            placeholder_text="描述（可选）",
            width=150
        )
        desc_entry.pack(anchor="w", pady=2)
        desc_entry.insert(0, material.get("desc", ""))
        desc_entry.bind("<FocusOut>", lambda e, t=material_type, i=index: self._update_desc(t, i, desc_entry.get()))

        # 删除按钮
        del_btn = ctk.CTkButton(
            item_frame,
            text="✕",
            width=28,
            height=28,
            corner_radius=6,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda t=material_type, i=index: self._delete_material(t, i)
        )
        del_btn.pack(side="right", padx=5)

    def _add_material(self):
        """添加素材（支持批量选择）"""
        material_type = self.current_tab.get()

        if material_type == "characters":
            # 检查数量限制
            current_count = len(self.materials["characters"])
            if current_count >= self.MAX_CHARACTERS:
                return

            # 批量选择图片
            file_paths = filedialog.askopenfilenames(
                title="选择人物图片（可多选）",
                filetypes=[
                    ("图片文件", "*.png *.jpg *.jpeg *.webp *.gif"),
                    ("所有文件", "*.*")
                ]
            )

            if file_paths:
                # 计算可添加的数量
                available_slots = self.MAX_CHARACTERS - current_count
                files_to_add = list(file_paths)[:available_slots]

                if len(file_paths) > available_slots:
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "提示",
                        f"人物素材最多 {self.MAX_CHARACTERS} 个，已为您选择前 {available_slots} 个文件"
                    )

                for file_path in files_to_add:
                    # 如果有项目目录，复制到 assets 目录
                    final_path = file_path
                    if self.get_project_dir:
                        project_dir = self.get_project_dir()
                        if project_dir:
                            from core.utils import FileUtils
                            import shutil
                            assets_dir = Path(project_dir) / "assets"
                            assets_dir.mkdir(parents=True, exist_ok=True)
                            filename = os.path.basename(file_path)
                            unique_name = FileUtils.get_unique_filename(str(assets_dir), filename)
                            dst_path = assets_dir / unique_name
                            shutil.copy2(file_path, dst_path)
                            final_path = str(dst_path)

                    filename = os.path.basename(final_path)
                    self.materials["characters"].append({
                        "name": os.path.splitext(filename)[0],
                        "desc": "",
                        "path": final_path,
                        "filename": filename
                    })

        elif material_type == "scenes":
            # 批量选择图片
            file_paths = filedialog.askopenfilenames(
                title="选择场景图片（可多选）",
                filetypes=[
                    ("图片文件", "*.png *.jpg *.jpeg *.webp *.gif"),
                    ("所有文件", "*.*")
                ]
            )

            if file_paths:
                for file_path in file_paths:
                    # 如果有项目目录，复制到 assets 目录
                    final_path = file_path
                    if self.get_project_dir:
                        project_dir = self.get_project_dir()
                        if project_dir:
                            from core.utils import FileUtils
                            import shutil
                            assets_dir = Path(project_dir) / "assets"
                            assets_dir.mkdir(parents=True, exist_ok=True)
                            filename = os.path.basename(file_path)
                            unique_name = FileUtils.get_unique_filename(str(assets_dir), filename)
                            dst_path = assets_dir / unique_name
                            shutil.copy2(file_path, dst_path)
                            final_path = str(dst_path)

                    filename = os.path.basename(final_path)
                    self.materials["scenes"].append({
                        "name": os.path.splitext(filename)[0],
                        "desc": "",
                        "path": final_path,
                        "filename": filename
                    })

        elif material_type == "voices":
            # 批量选择音频
            file_paths = filedialog.askopenfilenames(
                title="选择声线文件（可多选）",
                filetypes=[
                    ("音频文件", "*.mp3 *.wav *.ogg *.m4a"),
                    ("所有文件", "*.*")
                ]
            )

            if file_paths:
                for file_path in file_paths:
                    # 如果有项目目录，复制到 assets 目录
                    final_path = file_path
                    if self.get_project_dir:
                        project_dir = self.get_project_dir()
                        if project_dir:
                            from core.utils import FileUtils
                            import shutil
                            assets_dir = Path(project_dir) / "assets"
                            assets_dir.mkdir(parents=True, exist_ok=True)
                            filename = os.path.basename(file_path)
                            unique_name = FileUtils.get_unique_filename(str(assets_dir), filename)
                            dst_path = assets_dir / unique_name
                            shutil.copy2(file_path, dst_path)
                            final_path = str(dst_path)

                    filename = os.path.basename(final_path)
                    self.materials["voices"].append({
                        "name": os.path.splitext(filename)[0],
                        "desc": "",
                        "path": final_path,
                        "filename": filename
                    })

        # 刷新显示
        self._switch_tab()

        # 通知回调
        if self.on_material_change:
            self.on_material_change(material_type, self.materials[material_type])

    def _delete_material(self, material_type: str, index: int):
        """删除素材"""
        if 0 <= index < len(self.materials[material_type]):
            del self.materials[material_type][index]
            self._switch_tab()

            if self.on_material_change:
                self.on_material_change(material_type, self.materials[material_type])

    def _update_name(self, material_type: str, index: int, name: str):
        """更新名称"""
        if 0 <= index < len(self.materials[material_type]):
            self.materials[material_type][index]["name"] = name

            if self.on_material_change:
                self.on_material_change(material_type, self.materials[material_type])

    def _update_desc(self, material_type: str, index: int, desc: str):
        """更新描述"""
        if 0 <= index < len(self.materials[material_type]):
            self.materials[material_type][index]["desc"] = desc

            if self.on_material_change:
                self.on_material_change(material_type, self.materials[material_type])

    def _get_type_name(self, material_type: str) -> str:
        """获取类型名称"""
        names = {
            "characters": "人物",
            "scenes": "场景",
            "voices": "声线"
        }
        return names.get(material_type, material_type)

    def get_materials(self) -> Dict:
        """获取所有素材"""
        return self.materials

    def clear(self):
        """清空素材"""
        self.materials = {
            "characters": [],
            "scenes": [],
            "voices": []
        }
        self._switch_tab()