# -*- coding: utf-8 -*-
"""
片段表格组件
展示和管理视频片段
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Dict, Optional, Callable
from core.ai_engine import Segment
from core.utils import FileUtils
import os


class SegmentTable(ctk.CTkFrame):
    """片段表格组件"""

    # 即梦AI支持的时长选项（秒）
    DURATION_OPTIONS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    def __init__(self, master, on_prompt_edit: Callable = None,
                 on_video_upload: Callable = None,
                 on_generate_grid: Callable = None,
                 on_delete_segment: Callable = None,
                 on_add_segment: Callable = None,
                 on_add_reference: Callable = None,
                 on_delete_reference: Callable = None,
                 on_generate_video: Callable = None,
                 on_batch_generate_video: Callable = None,
                 get_assets_dir: Callable = None,
                 on_duration_edit: Callable = None,
                 is_safe_mode: Callable = None):
        super().__init__(master)

        self.on_prompt_edit = on_prompt_edit
        self.on_video_upload = on_video_upload
        self.on_generate_grid = on_generate_grid
        self.on_delete_segment = on_delete_segment
        self.on_add_segment = on_add_segment
        self.on_add_reference = on_add_reference
        self.on_delete_reference = on_delete_reference
        self.on_generate_video = on_generate_video
        self.on_batch_generate_video = on_batch_generate_video
        self.get_assets_dir = get_assets_dir
        self.on_duration_edit = on_duration_edit
        self.is_safe_mode = is_safe_mode  # 获取当前是否为安全模式的回调函数

        self.segments: List[Segment] = []
        self.materials: Dict = {}
        self.row_widgets: List[Dict] = []
        self.selected_indices: set = set()  # 存储勾选的片段索引

        self._create_ui()

    def _create_ui(self):
        """创建UI"""
        # 创建可滚动区域
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True)

        # 表头
        self._create_header()

        # 内容区域
        self.content_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

    def _create_header(self):
        """创建表头"""
        header_frame = ctk.CTkFrame(
            self.scroll_frame,
            height=45,
            fg_color="transparent",
            border_width=0,
            corner_radius=0
        )
        header_frame.pack(fill="x", pady=(0, 8))
        header_frame.pack_propagate(False)

        # 全选复选框 - 优化样式
        self.select_all_var = ctk.BooleanVar(value=False)
        self.select_all_checkbox = ctk.CTkCheckBox(
            header_frame,
            text="",
            variable=self.select_all_var,
            width=24,
            checkbox_height=20,
            checkbox_width=20,
            corner_radius=4,
            border_width=2,
            command=self._on_select_all
        )
        self.select_all_checkbox.pack(side="left", padx=(8, 12), pady=12)

        # 列宽配置 - 与行保持一致
        columns = [
            ("序号", 45),
            ("时长", 70),
            ("提示词", 350),
            ("视频", 140),
            ("引用", 160),
            ("操作", 500)
        ]

        for col_name, col_width in columns:
            label = ctk.CTkLabel(
                header_frame,
                text=col_name,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=col_width,
                text_color=["#4a5568", "#a0aec0"]
            )
            label.pack(side="left", padx=0, pady=12)

    def set_segments(self, segments: List[Segment], materials: Dict):
        """设置片段数据"""
        self.segments = segments
        self.materials = materials
        self._refresh_table()

    def clear(self):
        """清空表格"""
        self.segments = []
        self.materials = {}
        self._refresh_table()

    def _refresh_table(self):
        """刷新表格"""
        # 清除现有内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.row_widgets = []
        self.selected_indices = set()  # 重置选中状态
        self.select_all_var.set(False)  # 重置全选复选框

        if not self.segments:
            # 显示空状态
            empty_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无片段，请输入描述并点击「拆分片段」",
                text_color="gray"
            )
            empty_label.pack(pady=50)
            return

        # 创建每行
        for i, segment in enumerate(self.segments):
            row = self._create_row(i, segment)
            self.row_widgets.append(row)

    def _create_row(self, index: int, segment: Segment) -> Dict:
        """创建一行"""
        row_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent",
            border_width=0,
            corner_radius=0
        )
        row_frame.pack(fill="x", pady=1)

        widgets = {"frame": row_frame}

        # 勾选框 - 优化样式
        select_var = ctk.BooleanVar(value=index in self.selected_indices)
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=select_var,
            width=24,
            checkbox_height=20,
            checkbox_width=20,
            corner_radius=4,
            border_width=2,
            command=lambda idx=index, var=select_var: self._on_select_row(idx, var)
        )
        checkbox.pack(side="left", padx=(8, 12), pady=10)
        widgets["checkbox"] = checkbox
        widgets["select_var"] = select_var

        # 序号
        index_label = ctk.CTkLabel(
            row_frame,
            text=str(segment.index),
            width=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        index_label.pack(side="left", padx=0, pady=10)
        widgets["index"] = index_label

        # 时长（可编辑下拉框）
        current_duration = int(segment.duration) if segment.duration else 10
        duration_combo = ctk.CTkOptionMenu(
            row_frame,
            values=[f"{d}s" for d in self.DURATION_OPTIONS],
            width=70,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda value, idx=index: self._on_duration_change(idx, value)
        )
        duration_combo.set(f"{current_duration}s")
        duration_combo.pack(side="left", padx=0, pady=10)
        widgets["duration"] = duration_combo

        # 提示词（可编辑）
        prompt_text = ctk.CTkTextbox(row_frame, width=350, height=80)
        prompt_text.pack(side="left", padx=0)
        prompt_text.insert("1.0", segment.prompt)
        prompt_text.bind("<FocusOut>", lambda e, idx=index: self._on_prompt_change(idx, e))
        widgets["prompt"] = prompt_text

        # 视频列 - 垂直排列（状态在上，上传按钮在下）
        video_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        video_frame.pack(side="left", padx=0)

        if segment.video_path:
            video_status = "✅ 已上传"
            video_color = "green"
        else:
            video_status = "未上传"
            video_color = "gray"

        video_label = ctk.CTkLabel(
            video_frame,
            text=video_status,
            text_color=video_color,
            font=ctk.CTkFont(size=11)
        )
        video_label.pack(pady=(10, 2))
        widgets["video_status"] = video_label

        upload = ctk.CTkButton(
            video_frame,
            text="上传",
            width=120,
            height=28,
            fg_color="#3498db",
            hover_color="#2980b9",
            corner_radius=4,
            font=ctk.CTkFont(size=11),
            command=lambda idx=index: self._upload_video(idx)
        )
        upload.pack(pady=(0, 10))
        widgets["upload_btn"] = upload

        # 引用列 - 固定高度容器，与提示词列对齐
        ref_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        ref_frame.pack(side="left", padx=0)

        # 引用文件列表容器 - 普通Frame，限制显示数量保持行高稳定
        refs = segment.references or []
        ref_list_frame = ctk.CTkFrame(ref_frame, fg_color="transparent", border_width=0)
        ref_list_frame.pack(pady=0)

        if refs:
            # 最多显示3个文件，防止撑大行高
            display_refs = refs[:3]
            for ref_idx, ref_name in enumerate(display_refs):
                ref_label = ctk.CTkLabel(
                    ref_list_frame,
                    text=f"📄 {ref_name}",
                    width=140,
                    justify="left",
                    font=ctk.CTkFont(size=9, underline=True),
                    text_color="#3498db",
                    cursor="hand2"
                )
                ref_label.pack(anchor="w", pady=0)
                ref_label.bind("<Button-1>", lambda e, r=ref_name, idx=index: self._preview_reference(idx, r))
                ref_label.bind("<Button-3>", lambda e, idx=index, r=ref_name: self._quick_delete_reference(idx, r))

            # 超过3个显示省略
            if len(refs) > 3:
                more_label = ctk.CTkLabel(
                    ref_list_frame,
                    text=f"...+{len(refs) - 3}",
                    font=ctk.CTkFont(size=8),
                    text_color="gray"
                )
                more_label.pack(anchor="w")
        else:
            ref_label = ctk.CTkLabel(
                ref_list_frame,
                text="无",
                width=140,
                justify="left",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            ref_label.pack(anchor="w")

        widgets["references_frame"] = ref_list_frame

        # 底部：添加引用按钮
        add_ref = ctk.CTkButton(
            ref_frame,
            text="+",
            width=30,
            height=20,
            corner_radius=4,
            fg_color="#27ae60",
            hover_color="#229954",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda idx=index: self._add_reference(idx)
        )
        add_ref.pack(pady=(2, 0))
        widgets["add_ref_btn"] = add_ref

        # 操作列 - 所有按钮垂直排列
        action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        action_frame.pack(side="left", padx=0, pady=10)

        # 生成视频按钮
        gen_video = ctk.CTkButton(
            action_frame,
            text="生成视频",
            width=100,
            height=28,
            corner_radius=4,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            font=ctk.CTkFont(size=11),
            command=lambda idx=index: self._generate_video(idx)
        )
        gen_video.pack(pady=2)
        widgets["video_btn"] = gen_video

        # 九宫格按钮
        grid_btn = ctk.CTkButton(
            action_frame,
            text="九宫格",
            width=100,
            height=28,
            corner_radius=4,
            fg_color="#f39c12",
            hover_color="#e67e22",
            font=ctk.CTkFont(size=11),
            command=lambda idx=index: self._generate_grid(idx)
        )
        grid_btn.pack(pady=2)
        widgets["grid_btn"] = grid_btn

        # 删除按钮
        del_btn = ctk.CTkButton(
            action_frame,
            text="删除",
            width=100,
            height=28,
            corner_radius=4,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=ctk.CTkFont(size=11),
            command=lambda idx=index: self._delete_segment(idx)
        )
        del_btn.pack(pady=2)

        # 新增按钮
        add_btn = ctk.CTkButton(
            action_frame,
            text="新增",
            width=100,
            height=28,
            corner_radius=4,
            fg_color="#27ae60",
            hover_color="green",
            font=ctk.CTkFont(size=11),
            command=lambda idx=index: self._add_segment(idx)
        )
        add_btn.pack(pady=2)

        return widgets

    def _on_prompt_change(self, index: int, event):
        """提示词变更"""
        if 0 <= index < len(self.row_widgets):
            prompt_text = self.row_widgets[index]["prompt"]
            new_prompt = prompt_text.get("1.0", "end-1c")

            if self.on_prompt_edit:
                self.on_prompt_edit(index, new_prompt)

    def _on_duration_change(self, index: int, value: str):
        """时长变更"""
        if 0 <= index < len(self.segments):
            # 从 "Xs" 格式中提取数值
            try:
                new_duration = int(value.replace("s", ""))
                if self.on_duration_edit:
                    self.on_duration_edit(index, new_duration)
            except ValueError:
                pass

    def _upload_video(self, index: int):
        """上传视频"""
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.webm"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            # 更新显示
            if 0 <= index < len(self.row_widgets):
                self.row_widgets[index]["video_status"].configure(
                    text="✅ 已上传",
                    text_color="green"
                )

            if self.on_video_upload:
                self.on_video_upload(index, file_path)

    def _generate_grid(self, index: int):
        """生成九宫格"""
        if self.on_generate_grid:
            self.on_generate_grid(index)

    def _delete_segment(self, index: int):
        """删除片段"""
        if messagebox.askyesno("确认", f"确定要删除片段 {index + 1} 吗？"):
            if self.on_delete_segment:
                self.on_delete_segment(index)

    def _add_segment(self, index: int):
        """添加片段"""
        if self.on_add_segment:
            self.on_add_segment(index)

    def _add_reference(self, index: int):
        """添加引用 -从 assets 目录选择文件"""
        # 获取 assets 目录
        if self.get_assets_dir:
            assets_dir = self.get_assets_dir()
        else:
            assets_dir = None

        if not assets_dir or not os.path.exists(assets_dir):
            messagebox.showwarning("警告", "请先创建或打开项目")
            return

        # 获取 assets 目录中的文件列表
        try:
            files = []
            for f in os.listdir(assets_dir):
                file_path = os.path.join(assets_dir, f)
                if os.path.isfile(file_path):
                    # 只显示图片和视频文件
                    ext = os.path.splitext(f)[1].lower()
                    if ext in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.mp4', '.avi', '.mov', '.mkv'}:
                        files.append(f)
        except Exception as e:
            messagebox.showerror("错误", f"读取 assets 目录失败: {e}")
            return

        if not files:
            messagebox.showinfo("提示", "assets 目录中没有可用的文件\n请先上传素材或生成九宫格")
            return

        # 创建文件选择对话框
        self._show_file_selection_dialog(index, files, assets_dir)

    def _show_file_selection_dialog(self, index: int, files: List[str], assets_dir: str):
        """显示文件选择对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("选择引用文件")
        dialog.geometry("400x500")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # 存储选中的文件
        selected_files = []

        # 标题
        title_label = ctk.CTkLabel(
            dialog, text="选择要引用的文件（可多选）",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=10)

        # 提示信息
        hint_label = ctk.CTkLabel(
            dialog, text=f"文件来源: {assets_dir}",
            text_color="gray", font=ctk.CTkFont(size=11)
        )
        hint_label.pack(pady=(0, 10))

        # 文件列表框架
        list_frame = ctk.CTkScrollableFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 创建文件复选框
        file_vars = {}
        for file_name in sorted(files):
            var = ctk.BooleanVar(value=False)
            file_vars[file_name] = var

            # 创建文件项框架
            file_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
            file_frame.pack(fill="x", pady=2)

            checkbox = ctk.CTkCheckBox(
                file_frame,
                text=file_name,
                variable=var,
                font=ctk.CTkFont(size=12)
            )
            checkbox.pack(side="left", padx=5)

        # 底部按钮
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        def on_confirm():
            # 收集选中的文件
            selected = [f for f, v in file_vars.items() if v.get()]
            if selected:
                # 调用回调添加引用
                if self.on_add_reference:
                    self.on_add_reference(index, selected)
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请至少选择一个文件")

        def on_cancel():
            dialog.destroy()

        def on_select_all():
            for var in file_vars.values():
                var.set(True)

        def on_deselect_all():
            for var in file_vars.values():
                var.set(False)

        select_all_btn = ctk.CTkButton(
            btn_frame, text="全选", width=60,
            command=on_select_all, fg_color="gray"
        )
        select_all_btn.pack(side="left", padx=5)

        deselect_btn = ctk.CTkButton(
            btn_frame, text="取消全选", width=70,
            command=on_deselect_all, fg_color="gray"
        )
        deselect_btn.pack(side="left", padx=5)

        confirm_btn = ctk.CTkButton(
            btn_frame, text="确定", width=60,
            command=on_confirm
        )
        confirm_btn.pack(side="right", padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="取消", width=60,
            command=on_cancel, fg_color="gray"
        )
        cancel_btn.pack(side="right", padx=5)

    def _generate_video(self, index: int):
        """生成视频（即梦AI）"""
        if self.on_generate_video:
            self.on_generate_video(index)

    def _delete_reference(self, index: int):
        """删除引用 - 显示选择对话框让用户选择要删除的引用"""
        if not 0 <= index < len(self.segments):
            return

        segment = self.segments[index]
        refs = segment.references or []

        if not refs:
            messagebox.showinfo("提示", "该片段没有引用可删除")
            return

        # 创建引用选择对话框
        self._show_delete_reference_dialog(index, refs)

    def _show_delete_reference_dialog(self, index: int, refs: List[str]):
        """显示删除引用的选择对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("选择要删除的引用")
        dialog.geometry("400x450")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # 存储选中的引用
        selected_refs = []

        # 标题
        title_label = ctk.CTkLabel(
            dialog, text="选择要删除的引用（可多选）",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=10)

        # 提示信息
        hint_label = ctk.CTkLabel(
            dialog, text=f"片段 {index + 1} 当前有 {len(refs)} 个引用",
            text_color="gray", font=ctk.CTkFont(size=11)
        )
        hint_label.pack(pady=(0, 10))

        # 引用列表框架
        list_frame = ctk.CTkScrollableFrame(dialog)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 创建引用复选框
        ref_vars = {}
        for ref_name in refs:
            var = ctk.BooleanVar(value=False)
            ref_vars[ref_name] = var

            # 创建引用项框架
            ref_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
            ref_frame.pack(fill="x", pady=2)

            checkbox = ctk.CTkCheckBox(
                ref_frame,
                text=ref_name,
                variable=var,
                font=ctk.CTkFont(size=12)
            )
            checkbox.pack(side="left", padx=5)

        # 底部按钮
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        def on_confirm():
            # 收集选中的引用
            selected = [r for r, v in ref_vars.items() if v.get()]
            if selected:
                # 调用回调删除引用
                if self.on_delete_reference:
                    self.on_delete_reference(index, selected)
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "请至少选择一个引用")

        def on_cancel():
            dialog.destroy()

        def on_select_all():
            for var in ref_vars.values():
                var.set(True)

        def on_deselect_all():
            for var in ref_vars.values():
                var.set(False)

        select_all_btn = ctk.CTkButton(
            btn_frame, text="全选", width=60,
            command=on_select_all, fg_color="gray"
        )
        select_all_btn.pack(side="left", padx=5)

        deselect_btn = ctk.CTkButton(
            btn_frame, text="取消全选", width=70,
            command=on_deselect_all, fg_color="gray"
        )
        deselect_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="取消", width=60,
            command=on_cancel, fg_color="gray"
        )
        cancel_btn.pack(side="right", padx=5)

        confirm_btn = ctk.CTkButton(
            btn_frame, text="删除", width=60,
            command=on_confirm, fg_color="#e74c3c", hover_color="#c0392b"
        )
        confirm_btn.pack(side="right", padx=5)

    def _on_select_all(self):
        """全选/取消全选"""
        if self.select_all_var.get():
            # 全选
            self.selected_indices = set(range(len(self.segments)))
        else:
            # 取消全选
            self.selected_indices = set()

        # 更新每行的复选框状态
        for i, row in enumerate(self.row_widgets):
            select_var = row.get("select_var")
            if select_var:
                select_var.set(i in self.selected_indices)

    def _on_select_row(self, index: int, var: ctk.BooleanVar):
        """单行选择"""
        if var.get():
            self.selected_indices.add(index)
        else:
            self.selected_indices.discard(index)

        # 更新全选复选框状态
        if len(self.selected_indices) == len(self.segments) and len(self.segments) > 0:
            self.select_all_var.set(True)
        else:
            self.select_all_var.set(False)

    def get_selected_indices(self) -> List[int]:
        """获取选中的片段索引列表（按顺序排序）"""
        return sorted(list(self.selected_indices))

    def clear_selection(self):
        """清空选择"""
        self.selected_indices = set()
        self.select_all_var.set(False)
        for row in self.row_widgets:
            select_var = row.get("select_var")
            if select_var:
                select_var.set(False)

    def _preview_reference(self, index: int, ref_name: str):
        """预览引用文件"""
        if not self.get_assets_dir:
            return

        assets_dir = self.get_assets_dir()
        if not assets_dir:
            return

        file_path = os.path.join(assets_dir, ref_name)
        if not os.path.exists(file_path):
            messagebox.showwarning("警告", f"文件不存在: {ref_name}")
            return

        # 根据文件类型选择预览方式
        ext = os.path.splitext(ref_name)[1].lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}

        if ext in image_exts:
            # 图片预览
            self._show_image_preview(file_path, ref_name)
        elif ext in video_exts:
            # 视频预览 - 使用系统默认程序打开
            self._open_with_system(file_path)
        else:
            # 其他文件 - 使用系统默认程序打开
            self._open_with_system(file_path)

    def _show_image_preview(self, file_path: str, file_name: str):
        """显示图片预览窗口"""
        try:
            from PIL import Image, ImageTk

            # 创建预览窗口
            preview_window = ctk.CTkToplevel(self)
            preview_window.title(f"预览: {file_name}")
            preview_window.geometry("800x600")
            preview_window.transient(self.winfo_toplevel())

            # 加载图片
            img = Image.open(file_path)

            # 计算缩放比例以适应窗口
            max_width, max_height = 780, 550
            img_width, img_height = img.size
            scale = min(max_width / img_width, max_height / img_height, 1.0)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            if scale < 1.0:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 转换为 CTkImage
            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_width, new_height))

            # 显示图片
            img_label = ctk.CTkLabel(preview_window, image=ctk_image, text="")
            img_label.image = ctk_image  # 保持引用
            img_label.pack(pady=10)

            # 文件信息
            info_label = ctk.CTkLabel(
                preview_window,
                text=f"文件: {file_name} | 原始尺寸: {img_width}×{img_height}",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            info_label.pack(pady=5)

            # 打开文件夹按钮
            def open_folder():
                import subprocess
                import sys
                folder_path = os.path.dirname(file_path)
                if sys.platform == 'win32':
                    subprocess.run(['explorer', folder_path])
                elif sys.platform == 'darwin':
                    subprocess.run(['open', folder_path])
                else:
                    subprocess.run(['xdg-open', folder_path])

            open_folder_btn = ctk.CTkButton(
                preview_window,
                text="打开所在文件夹",
                command=open_folder,
                fg_color="gray",
                width=120
            )
            open_folder_btn.pack(pady=10)

        except Exception as e:
            messagebox.showerror("错误", f"无法预览图片: {e}")
            # 尝试用系统程序打开
            self._open_with_system(file_path)

    def _open_with_system(self, file_path: str):
        """使用系统默认程序打开文件"""
        import subprocess
        import sys

        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {e}")

    def _quick_delete_reference(self, index: int, ref_name: str):
        """快速删除单个引用文件"""
        if messagebox.askyesno("确认删除", f"确定要删除引用「{ref_name}」吗？"):
            if self.on_delete_reference:
                self.on_delete_reference(index, [ref_name])
