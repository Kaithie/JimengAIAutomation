# -*- coding: utf-8 -*-
"""
即梦视频自动生成模块
通过 Playwright 自动化控制即梦AI视频生成平台
"""

import os
import re
import time
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path
import threading


# 全局浏览器管理器（线程安全锁）
_browser_lock = threading.Lock()
_global_playwright = None
_global_context = None
_global_user_data_dir = None


class JimengVideoAutomation:
    """即梦视频自动生成类"""

    # 即梦主页 URL
    JIMENG_HOME_URL = "https://jimeng.jianying.com/ai-tool/home/?type=video"

    # 支持的文件类型
    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.avi'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav'}

    def __init__(self, headless: bool = False, on_progress: Callable = None):
        """
        初始化即梦视频自动化器

        Args:
            headless: 是否使用无头模式
            on_progress: 进度回调函数
        """
        self.headless = headless
        self.on_progress = on_progress
        self.browser = None
        self.context = None
        self.page = None
        self._owns_browser = False  # 标记是否由该实例创建/拥有浏览器

    def _report_progress(self, message: str, step: int = 0, total: int = 0):
        """报告进度"""
        if self.on_progress:
            self.on_progress(message, step, total)
        print(f"[即梦] {message}")

    def _get_user_data_dir(self) -> str:
        """获取浏览器用户数据目录"""
        user_data_dir = Path.home() / ".jimeng-browser-data"
        return str(user_data_dir)

    def start_browser(self) -> bool:
        """启动浏览器（复用已打开的浏览器）"""
        global _global_playwright, _global_context, _global_user_data_dir

        try:
            from playwright.sync_api import sync_playwright

            user_data_dir = self._get_user_data_dir()

            # 使用锁确保线程安全
            with _browser_lock:
                # 检查是否已有全局浏览器实例
                if _global_context is not None:
                    # 验证浏览器是否真的还在运行
                    browser_alive = False
                    try:
                        # 尝试获取浏览器信息来验证是否存活
                        # 如果浏览器已关闭，这个操作会抛出异常
                        _ = _global_context.pages
                        browser_alive = True
                    except Exception:
                        # 浏览器已关闭，清理旧引用
                        self._report_progress("检测到浏览器已关闭，正在重新启动...", 1, 7)
                        try:
                            _global_context.close()
                        except:
                            pass
                        try:
                            _global_playwright.stop()
                        except:
                            pass
                        _global_playwright = None
                        _global_context = None
                        _global_user_data_dir = None

                    if browser_alive:
                        self._report_progress("检测到已打开的浏览器，正在创建新标签页...", 1, 7)
                        self.playwright = _global_playwright
                        self.context = _global_context
                        self._owns_browser = False

                if _global_context is None:
                    # 创建新的浏览器实例
                    self._report_progress("正在启动浏览器...", 1, 7)

                    self.playwright = sync_playwright().start()
                    self.context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=self.headless,
                        args=["--disable-blink-features=AutomationControlled"],
                        viewport={"width": 1400, "height": 1000},
                    )

                    # 保存到全局变量
                    _global_playwright = self.playwright
                    _global_context = self.context
                    _global_user_data_dir = user_data_dir
                    self._owns_browser = True

                # 创建新页面（标签页）
                self.page = self.context.new_page()

            return True
        except Exception as e:
            self._report_progress(f"启动浏览器失败: {e}")
            return False

    def close_browser(self):
        """关闭浏览器（只关闭当前页面，不关闭全局浏览器）"""
        global _global_playwright, _global_context, _global_user_data_dir

        try:
            # 只关闭当前页面（标签页），不关闭整个浏览器
            if self.page:
                try:
                    self.page.close()
                except:
                    pass
                self.page = None

            # 只关闭自己创建的浏览器（全局情况下不关闭）
            if self._owns_browser:
                with _browser_lock:
                    try:
                        if self.context:
                            self.context.close()
                        if self.playwright:
                            self.playwright.stop()
                        # 清空全局变量
                        _global_playwright = None
                        _global_context = None
                        _global_user_data_dir = None
                    except:
                        pass
        except:
            pass

        self.browser = None
        self.context = None
        self._owns_browser = False

    def open_jimeng_home(self) -> bool:
        """打开即梦主页"""
        try:
            self._report_progress("正在打开即梦主页...", 2, 7)

            self.page.goto(self.JIMENG_HOME_URL, wait_until="domcontentloaded", timeout=60000)

            # 等待关键元素出现（模式下拉框），而不是固定时间等待
            try:
                self.page.wait_for_selector('div[role="combobox"]', timeout=30000)
                self._report_progress("页面加载完成")
            except Exception as e:
                self._report_progress(f"等待页面元素超时，尝试继续: {e}")

            # 清除输入框焦点，防止 Enter 键误触发提交
            try:
                self.page.mouse.click(10, 10)
                time.sleep(0.2)
            except:
                pass

            return True
        except Exception as e:
            self._report_progress(f"打开即梦主页失败: {e}")
            return False

    def switch_to_reference_mode(self) -> bool:
        """切换到全能参考模式"""
        time.sleep(2)

        # 尝试多种方式定位下拉框
        combobox = None
        combobox_selectors = [
            'div[role="combobox"]',
            'div:has-text("首尾帧")',
            'div:has-text("智能多帧")',
            'div:has-text("主体参考")',
            '[class*="select"]',
            '[class*="dropdown"]',
            '[class*="mode-select"]',
        ]

        for selector in combobox_selectors:
            try:
                elements = self.page.locator(selector)
                count = elements.count()
                for i in range(count):
                    el = elements.nth(i)
                    text = el.inner_text(timeout=500)
                    if '首尾帧' in text or '智能多帧' in text or '主体参考' in text:
                        if el.is_visible(timeout=1000):
                            combobox = el
                            self._report_progress(f"找到模式下拉框，文本: {text}")
                            break
                if combobox:
                    break
            except:
                continue

        if not combobox:
            self._report_progress("未找到模式下拉框，可能已是全能参考模式")
            return True  # 不算失败，可能已经是该模式

        # 点击展开下拉框
        combobox.click()
        time.sleep(1)

        # 选择"全能参考"选项
        option_selectors = [
            'li:has-text("全能参考")',
            'div:has-text("全能参考")',
            '[role="option"]:has-text("全能参考")',
            'text="全能参考"',
        ]

        clicked = False
        for selector in option_selectors:
            try:
                option = self.page.locator(selector).first
                if option.is_visible(timeout=2000):
                    option.click()
                    clicked = True
                    self._report_progress("已切换到全能参考模式")
                    break
            except:
                continue

        if not clicked:
            self._report_progress("未找到全能参考选项，可能已是该模式")

        time.sleep(1)
        return True

    def upload_files(self, file_paths: List[str]) -> bool:
        """
        上传参考文件

        Args:
            file_paths: 文件路径列表（按顺序上传）

        Returns:
            是否成功
        """
        try:
            self._report_progress(f"正在上传 {len(file_paths)} 个文件...", 4, 7)

            # 按文件名顺序上传
            for i, file_path in enumerate(file_paths):
                if not os.path.exists(file_path):
                    self._report_progress(f"文件不存在: {file_path}")
                    continue

                self._report_progress(f"上传文件 {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")

                # 定位文件上传 input
                file_input = self.page.locator('input[type="file"]').first
                file_input.set_input_files(file_path)
                time.sleep(1)  # 等待上传完成

            return True
        except Exception as e:
            self._report_progress(f"上传文件失败: {e}")
            return False

    def fill_prompt(self, prompt: str, references: List[Dict] = None) -> bool:
        """
        填写提示词

        Args:
            prompt: 提示词文本
            references: 引用信息列表 [{"filename": "xxx.png", "display_name": "角色A"}]

        Returns:
            是否成功
        """
        try:
            self._report_progress("正在填写提示词...", 5, 7)

            # 先清除焦点，防止残留的键盘事件
            try:
                self.page.mouse.click(10, 10)
                time.sleep(0.3)
            except:
                pass

            # 定位输入框
            editable_elements = self.page.locator('[contenteditable="true"], textarea')
            prompt_input = editable_elements.first

            # 点击输入框获取焦点
            prompt_input.click()
            time.sleep(0.3)

            # 清空现有内容
            self.page.keyboard.press("Control+A")
            time.sleep(0.1)

            # 如果有引用信息，需要特殊处理 @ 符号
            if references:
                self._fill_prompt_with_references(prompt, references)
            else:
                # 直接输入提示词，将普通回车替换为 Shift+Enter 避免自动提交
                self._type_prompt_with_linebreaks(prompt)

            # 填写完成后清除焦点，防止 Enter 键误触发
            try:
                self.page.mouse.click(10, 10)
                time.sleep(0.2)
            except:
                pass

            return True
        except Exception as e:
            self._report_progress(f"填写提示词失败: {e}")
            return False

    def _type_prompt_with_linebreaks(self, text: str):
        """
        输入文本，将普通回车替换为 Shift+Enter 以避免自动提交

        Args:
            text: 要输入的文本
        """
        # 按换行符分割文本
        parts = text.split('\n')

        # 输入第一个部分
        if parts[0]:
            self.page.keyboard.type(parts[0], delay=30)

        # 输入剩余部分，每个部分前面加 Shift+Enter
        for part in parts[1:]:
            if part or len(parts) > 1:  # 空行也需要换行
                self.page.keyboard.press('Shift+Enter')
                time.sleep(0.1)
                if part:
                    self.page.keyboard.type(part, delay=30)

    def _fill_prompt_with_references(self, prompt: str, references: List[Dict]):
        """
        填写包含引用的提示词（参考 D:\jimeng-auto 正常工作的实现）

        Args:
            prompt: 提示词文本
            references: 引用信息列表，包含 filename 和 upload_index（上传顺序索引）
        """
        # 构建文件名到上传顺序索引的映射
        filename_to_index = {}
        for ref in references:
            filename = ref.get("filename")
            upload_index = ref.get("upload_index", 0)
            if filename:
                filename_to_index[filename] = upload_index

        # 解析提示词，找到所有 @[文件名] 格式的引用
        pattern = r'@\[([^\]]+)\]'

        last_end = 0
        for match in re.finditer(pattern, prompt):
            # 输入 @ 之前的内容（使用 Shift+Enter 处理换行，避免自动提交）
            before_text = prompt[last_end:match.start()]
            if before_text:
                self._type_prompt_with_linebreaks(before_text)

            filename = match.group(1)

            # 输入 @ 触发下拉框
            self.page.keyboard.type("@", delay=50)
            time.sleep(0.5)  # 等待下拉框出现

            # 获取该文件的上传顺序索引
            upload_index = filename_to_index.get(filename, 0)

            # 调用独立的下拉选择方法
            self._select_file_from_dropdown(upload_index)

            last_end = match.end()

        # 输入剩余内容（使用 Shift+Enter 处理换行，避免自动提交）
        remaining_text = prompt[last_end:]
        if remaining_text:
            self._type_prompt_with_linebreaks(remaining_text)

    def _select_file_from_dropdown(self, file_index: int):
        """
        从 @ 触发的下拉框中选择文件（参考 D:\jimeng-auto 正常工作的实现）

        Args:
            file_index: 要选择的文件索引（从 0 开始）
        """
        self._report_progress("等待文件下拉框出现...")

        time.sleep(0.5)

        # 尝试定位下拉框选项（使用 :visible 伪选择器）
        option_selectors = [
            'li:visible',
            '[role="option"]:visible',
            'div[class*="item"]:visible',
            'div[role="listitem"]:visible',
        ]

        options = None
        for selector in option_selectors:
            try:
                found = self.page.locator(selector)
                if found.count() > 0:
                    options = found
                    break
            except:
                continue

        if not options or options.count() == 0:
            self._report_progress("未检测到下拉框选项")
            return

        option_count = options.count()
        self._report_progress(f"检测到 {option_count} 个下拉选项")

        # 验证索引
        if file_index >= option_count:
            self._report_progress(f"警告: 文件索引 {file_index} 超出范围，将选择第一个")
            file_index = 0

        # 选择对应索引的文件
        try:
            target_option = options.nth(file_index)
            if target_option.is_visible(timeout=2000):
                target_option.click()
                time.sleep(0.3)
                self._report_progress(f"已选择第 {file_index + 1} 个文件")
        except Exception as e:
            self._report_progress(f"点击选项失败: {e}")
            # 尝试键盘选择
            try:
                for _ in range(file_index):
                    self.page.keyboard.press('ArrowDown')
                    time.sleep(0.1)
                self.page.keyboard.press('Enter')
                self._report_progress(f"使用键盘选择第 {file_index + 1} 个文件")
            except Exception as e2:
                self._report_progress(f"键盘选择也失败: {e2}")

    def set_ratio_and_duration(self, ratio: str = "16:9", duration: int = 5) -> bool:
        """
        设置画面比例和视频时长

        Args:
            ratio: 画面比例 (16:9, 9:16, 1:1 等)
            duration: 视频时长（秒）

        Returns:
            是否成功
        """
        try:
            self._report_progress(f"设置比例 {ratio}，时长 {duration}秒...", 6, 7)

            # 先清除焦点，防止残留的键盘事件影响后续操作
            try:
                self.page.mouse.click(10, 10)
                time.sleep(0.3)
            except:
                pass

            # 等待页面稳定，确保所有元素都加载完成
            time.sleep(1.5)

            # ===== 设置比例 =====
            # 即梦的比例选择器是下拉选择器，需要先点击展开，再选择目标比例
            all_ratios = ["16:9", "21:9", "4:3", "3:4", "1:1", "9:16"]
            ratio_set = False

            for attempt in range(3):  # 最多尝试3次
                if ratio_set:
                    break

                try:
                    self._report_progress(f"尝试设置比例 ({attempt + 1}/3)...")

                    # 先清除焦点，防止误操作
                    try:
                        self.page.mouse.click(10, 10)
                        time.sleep(0.2)
                    except:
                        pass

                    # 第一步：找到比例选择器（显示当前比例的那个元素）
                    ratio_selector = None
                    current_ratio_text = None

                    # 遍历所有可能的元素，找到显示比例值的那个
                    try:
                        all_clickables = self.page.locator('button:visible, div[role="button"]:visible, div[role="combobox"]:visible, span:visible')
                        count = all_clickables.count()
                        self._report_progress(f"检查 {count} 个可点击元素...")

                        for i in range(count):
                            try:
                                el = all_clickables.nth(i)
                                text = el.inner_text(timeout=300).strip()
                                # 检查是否包含比例值
                                for r in all_ratios:
                                    if r in text and len(text) < 15:
                                        ratio_selector = el
                                        current_ratio_text = text
                                        self._report_progress(f"找到比例选择器 [{text}]")
                                        break
                                if ratio_selector:
                                    break
                            except:
                                continue
                    except Exception as e:
                        self._report_progress(f"遍历元素失败: {e}")

                    if ratio_selector:
                        # 获取选择器显示的当前比例
                        current_ratio = None
                        for r in all_ratios:
                            if r in (current_ratio_text or ""):
                                current_ratio = r
                                break

                        self._report_progress(f"当前比例: {current_ratio}, 目标比例: {ratio}")

                        # 如果当前已经是目标比例，跳过
                        if current_ratio == ratio:
                            self._report_progress(f"✓ 当前已是目标比例: {ratio}")
                            ratio_set = True
                            continue

                        # 第二步：点击展开下拉列表
                        ratio_selector.click()
                        time.sleep(1.0)  # 等待下拉动画完成
                        self._report_progress("已展开比例下拉列表")

                        # 第三步：在下拉列表中选择目标比例
                        # 即梦的下拉选项可能是 div 或其他元素，尝试多种选择器
                        option_clicked = False

                        # 方式1：直接查找包含目标比例文本的可见元素
                        try:
                            # 使用更通用的选择器，查找所有可见的包含目标比例的元素
                            candidates = self.page.locator(f'*:visible:has-text("{ratio}")')
                            cand_count = candidates.count()
                            self._report_progress(f"找到 {cand_count} 个包含 '{ratio}' 的可见元素")

                            for i in range(cand_count):
                                try:
                                    el = candidates.nth(i)
                                    text = el.inner_text(timeout=500).strip()
                                    # 精确匹配比例文本
                                    if text == ratio:
                                        # 确保这个元素是下拉选项而不是选择器本身
                                        el.click()
                                        option_clicked = True
                                        self._report_progress(f"方式1: 选择比例选项 '{text}'")
                                        break
                                except:
                                    continue
                        except Exception as e:
                            self._report_progress(f"方式1失败: {e}")

                        # 方式2：查找下拉面板中的选项
                        if not option_clicked:
                            try:
                                # 下拉面板通常是 ul 或 div 容器
                                panel_selectors = [
                                    'ul li',
                                    '[role="listbox"] div',
                                    '[role="listbox"] li',
                                    'div[class*="dropdown"] div',
                                    'div[class*="menu"] div',
                                    'div[class*="option"]',
                                ]
                                for ps in panel_selectors:
                                    try:
                                        items = self.page.locator(ps)
                                        if items.count() > 0:
                                            self._report_progress(f"使用选择器 '{ps}' 找到 {items.count()} 个选项")
                                            for i in range(items.count()):
                                                try:
                                                    item = items.nth(i)
                                                    if item.is_visible(timeout=500):
                                                        text = item.inner_text(timeout=300).strip()
                                                        if text == ratio:
                                                            item.click()
                                                            option_clicked = True
                                                            self._report_progress(f"方式2: 选择比例选项 '{text}'")
                                                            break
                                                except:
                                                    continue
                                            if option_clicked:
                                                break
                                    except:
                                        continue
                            except Exception as e:
                                self._report_progress(f"方式2失败: {e}")

                        # 方式3：遍历所有可见的 div 和 span，找到精确匹配目标比例的
                        if not option_clicked:
                            try:
                                all_divs = self.page.locator('div:visible, span:visible')
                                div_count = all_divs.count()
                                self._report_progress(f"方式3: 检查 {div_count} 个 div/span 元素")

                                for i in range(div_count):
                                    try:
                                        el = all_divs.nth(i)
                                        text = el.inner_text(timeout=100).strip()
                                        if text == ratio:
                                            # 找到精确匹配，尝试点击
                                            el.click()
                                            option_clicked = True
                                            self._report_progress(f"方式3: 选择比例选项 '{text}'")
                                            break
                                    except:
                                        continue
                            except Exception as e:
                                self._report_progress(f"方式3失败: {e}")

                        if option_clicked:
                            time.sleep(0.5)
                            ratio_set = True
                            self._report_progress(f"✓ 已设置比例: {ratio}")
                        else:
                            self._report_progress(f"未在下拉列表中找到比例选项: {ratio}")
                            # 点击空白处关闭下拉列表
                            try:
                                self.page.mouse.click(10, 10)
                            except:
                                pass
                    else:
                        self._report_progress(f"第 {attempt + 1} 次未找到比例选择器，等待后重试...")
                        time.sleep(1)

                except Exception as e:
                    self._report_progress(f"设置比例异常 ({attempt + 1}/3): {e}")
                    time.sleep(1)

            if not ratio_set:
                self._report_progress(f"⚠️ 未能设置比例 {ratio}，将使用当前比例")

            time.sleep(0.5)

            # ===== 设置时长 =====
            try:
                # 支持的时长选项
                duration_options = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

                # 先尝试直接找到显示当前时长的下拉框并点击
                # 即梦网站的时长下拉框通常显示如 "5s" 格式
                duration_el = None

                # 方式1：查找显示具体时长的下拉框（如 "5s"）
                for d in duration_options:
                    try:
                        # 查找显示当前时长的元素（可能是下拉框或按钮）
                        selector = f'div[role="combobox"]:has-text("{d}s")'
                        elements = self.page.locator(selector)
                        count = elements.count()
                        for i in range(count):
                            el = elements.nth(i)
                            text = el.inner_text(timeout=500).strip()
                            # 精确匹配，确保是时长选择器而不是其他带"s"的元素
                            if text == f"{d}s" or f"{d}s" in text and len(text) < 10:
                                if el.is_visible(timeout=1000):
                                    duration_el = el
                                    self._report_progress(f"找到时长下拉框，当前显示: {text}")
                                    break
                        if duration_el:
                            break
                    except:
                        continue

                # 方式2：如果没有找到，尝试查找包含多个时长选项的区域
                if not duration_el:
                    try:
                        # 查找包含时长时间选择特征的元素
                        # 通常是包含 "s" 后缀数字的下拉框
                        all_comboboxes = self.page.locator('div[role="combobox"]')
                        count = all_comboboxes.count()
                        for i in range(count):
                            el = all_comboboxes.nth(i)
                            text = el.inner_text(timeout=500)
                            # 检查是否包含时长特征（数字+s 格式）
                            if re.search(r'\d+s', text):
                                if el.is_visible(timeout=1000):
                                    duration_el = el
                                    self._report_progress(f"找到时长下拉框: {text}")
                                    break
                    except:
                        pass

                if duration_el:
                    # 点击展开下拉框
                    duration_el.click()
                    time.sleep(0.8)

                    # 选择目标时长选项
                    try:
                        # 尝试多种选择器定位选项
                        option_selectors = [
                            f'li:has-text("{duration}s")',
                            f'div:has-text("{duration}s")',
                            f'span:has-text("{duration}s")',
                            f'text="{duration}s"',
                        ]

                        clicked = False
                        for selector in option_selectors:
                            try:
                                option = self.page.locator(selector).first
                                if option.is_visible(timeout=1000):
                                    option.click()
                                    clicked = True
                                    self._report_progress(f"已设置时长: {duration}s")
                                    break
                            except:
                                continue

                        if not clicked:
                            # 尝试在所有可见选项中查找
                            all_options = self.page.locator('li:visible, [role="option"]:visible')
                            opt_count = all_options.count()
                            for i in range(opt_count):
                                try:
                                    opt = all_options.nth(i)
                                    opt_text = opt.inner_text(timeout=500)
                                    if f"{duration}s" in opt_text:
                                        opt.click()
                                        self._report_progress(f"已设置时长: {duration}s")
                                        clicked = True
                                        break
                                except:
                                    continue

                            if not clicked:
                                self._report_progress(f"未找到时长选项 {duration}s，使用当前选择")

                    except Exception as e:
                        self._report_progress(f"选择时长选项失败: {e}")
                else:
                    self._report_progress(f"未找到时长选择器，将使用默认时长")

            except Exception as e:
                self._report_progress(f"设置时长跳过: {e}")

            time.sleep(0.5)
            return True

        except Exception as e:
            self._report_progress(f"设置参数失败: {e}")
            return False

    def submit_generation(self) -> bool:
        """
        提交生成请求

        Returns:
            是否成功
        """
        try:
            self._report_progress("正在提交生成...", 7, 7)

            # 等待页面稳定，防止上一个操作的 Enter 被误触发
            time.sleep(1)

            # 清除输入框焦点，确保干净状态
            try:
                self.page.mouse.click(10, 10)
                time.sleep(0.3)
            except:
                pass

            # 点击对话框（输入框）
            input_box = self.page.locator('textarea, [contenteditable="true"]').first
            input_box.click()
            time.sleep(0.3)

            # 按 Enter 回车提交
            self.page.keyboard.press('Enter')
            time.sleep(0.5)

            # 提交后立即清除焦点，防止后续误触发
            try:
                self.page.mouse.click(10, 10)
            except:
                pass

            self._report_progress("已提交生成请求，请等待视频生成完成")

            return True
        except Exception as e:
            self._report_progress(f"提交生成失败: {e}")
            return False

    def wait_for_manual_submit(self):
        """
        等待用户手动提交（安全模式下）
        """
        self._report_progress("已填写完成，请手动审查参数并按 Enter 提交", 6, 7)
        self._report_progress("浏览器保持打开，您可以调整参数后再提交")

    def generate_video(self, prompt: str, file_paths: List[str],
                       references: List[Dict] = None,
                       ratio: str = "16:9",
                       duration: int = 5,
                       auto_submit: bool = True) -> Tuple[bool, str]:
        """
        完整的视频生成流程

        Args:
            prompt: 提示词
            file_paths: 参考文件路径列表
            references: 引用信息列表
            ratio: 画面比例
            duration: 视频时长
            auto_submit: 是否自动提交生成请求

        Returns:
            (是否成功, 消息)
        """
        try:
            # 1. 启动浏览器
            if not self.start_browser():
                return False, "启动浏览器失败"

            # 2. 打开即梦主页
            if not self.open_jimeng_home():
                return False, "打开即梦主页失败"

            # 3. 切换到全能参考模式
            if not self.switch_to_reference_mode():
                return False, "切换模式失败"

            # 4. 上传文件
            if file_paths:
                if not self.upload_files(file_paths):
                    return False, "上传文件失败"

            # 5. 填写提示词
            if not self.fill_prompt(prompt, references):
                return False, "填写提示词失败"

            # 6. 设置参数
            self.set_ratio_and_duration(ratio, duration)

            # 7. 根据模式选择是否自动提交
            if auto_submit:
                if not self.submit_generation():
                    return False, "提交生成失败"
                return True, "视频生成请求已提交，请在浏览器中查看进度"
            else:
                # 安全模式：不自动提交，等待用户手动操作
                self.wait_for_manual_submit()
                return True, "已填写完成（安全模式），请手动检查参数后提交"

        except Exception as e:
            return False, f"生成失败: {str(e)}"

    @staticmethod
    def close_global_browser():
        """全局关闭浏览器（在所有批量操作完成后调用）"""
        global _global_playwright, _global_context, _global_user_data_dir

        with _browser_lock:
            try:
                if _global_context:
                    _global_context.close()
                if _global_playwright:
                    _global_playwright.stop()
                _global_playwright = None
                _global_context = None
                _global_user_data_dir = None
                print("[即梦] 已关闭全局浏览器")
            except Exception as e:
                print(f"[即梦] 关闭全局浏览器失败: {e}")


def extract_references_from_prompt(prompt: str) -> List[str]:
    """
    从提示词中提取引用的文件名

    Args:
        prompt: 提示词文本

    Returns:
        引用的文件名列表（按出现顺序，去重）
    """
    pattern = r'@\[([^\]]+)\]'
    matches = re.findall(pattern, prompt)
    # 保持顺序去重
    seen = set()
    result = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def generate_jimeng_video_for_segment(
    segment,
    assets_dir: str,
    on_progress: Callable = None,
    headless: bool = False,
    auto_submit: bool = True
) -> Tuple[bool, str]:
    """
    为片段生成即梦视频

    Args:
        segment: Segment 对象
        assets_dir: assets 目录路径
        on_progress: 进度回调
        headless: 是否无头模式
        auto_submit: 是否自动提交生成请求（安全模式下为 False）

    Returns:
        (是否成功, 消息)
    """
    # 从提示词中提取引用
    referenced_files = extract_references_from_prompt(segment.prompt)

    # 也从 segment.references 中获取引用
    all_references = list(segment.references) if segment.references else []

    # 合并并去重，保持顺序
    for f in referenced_files:
        if f not in all_references:
            all_references.append(f)

    # 获取文件的完整路径，并记录上传顺序索引
    file_paths = []
    references_info = []

    for upload_index, filename in enumerate(all_references):
        file_path = os.path.join(assets_dir, filename)
        if os.path.exists(file_path):
            file_paths.append(file_path)
            references_info.append({
                "filename": filename,
                "display_name": os.path.splitext(filename)[0],
                "upload_index": upload_index  # 上传顺序索引，从 0 开始
            })

    # 获取片段时长（默认 5 秒）
    video_duration = int(segment.duration) if segment.duration else 5

    # 创建自动化实例
    automation = JimengVideoAutomation(
        headless=headless,
        on_progress=on_progress
    )

    try:
        success, message = automation.generate_video(
            prompt=segment.prompt,
            file_paths=file_paths,
            references=references_info,
            ratio="16:9",  # 固定使用 16:9 比例
            duration=video_duration,  # 传递时长参数
            auto_submit=auto_submit  # 传递是否自动提交
        )
        return (success, message)
    finally:
        # 不立即关闭浏览器，让用户查看进度
        # automation.close_browser()
        pass
