# -*- coding: utf-8 -*-
# GUI模块 - 主窗口实�?
# 使用 CustomTkinter 实现图形界面，解�?Tkinter �?Windows 上的主题渲染问题
# 所有颜色统一�?config.json 读取
# GUI Module - Main window implementation
# Uses CustomTkinter for graphical interface to solve Tkinter theme rendering issues on Windows
# All colors read from config.json

# 导入日志记录库
import logging
# 导入日期时间处理库
import datetime
# 导入 CustomTkinter 图形界面库
import customtkinter as ctk
# 导入标准 tkinter 用于部分兼容功能
import tkinter as tk
# 从 tkinter 导入 ttk 主题组件（Combobox 的原生箭头样式比 CTkOptionMenu 美观）
# Import ttk themed widgets from tkinter (Combobox native arrow looks better than CTkOptionMenu)
from tkinter import ttk
# 从 tkinter 导入消息框
from tkinter import messagebox

# �?i18n 模块导入翻译函数
from .i18n import _, set_language, get_current_language, get_supported_languages, get_language_name
# autostart_helper 的注册表操作已移至 app_controller.py 调用
# Registry operations from autostart_helper are now called in app_controller.py
# 从theme_manager模块导入主题颜色管理类、字体函数和主题常量
# Import theme color manager, font function and theme constants from theme_manager module
from .theme_manager import ThemeColors, get_font_family, get_font_size, set_font_scale, THEME_LIGHT, THEME_DARK
# 从app_controller模块导入应用控制器类（封装配置管理、自启动等纯业务逻辑）
# Import app controller class from app_controller module (config management, auto-start, etc.)
from .app_controller import AppController

# 创建本模块的日志记录�?
logger = logging.getLogger("VoiceInput")

# 字体映射表、get_font_family 函数已移至 theme_manager.py
# Font mapping and get_font_family function moved to theme_manager.py


class FloatingWindow:
    # 悬浮窗类 - 使用 CustomTkinter 实现
    
    def __init__(self, parent=None):
        self._parent = parent
        self._window = ctk.CTkToplevel(parent)
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", 0.92)
        self._setup_ui()
        self._drag_data = {"x": 0, "y": 0}
        self._window.bind("<Button-1>", self._on_drag_start)
        self._window.bind("<B1-Motion>", self._on_dragging)

    def _setup_ui(self):
        # 统一从 config.json 读取颜色
        c = ThemeColors()
        if self._parent and hasattr(self._parent, 'colors'):
            if self._parent.colors.dark_mode:
                c.apply_dark()
            else:
                c.apply_light()
        else:
            c.apply_dark()

        # 悬浮窗加细蓝色外边框：外层用主题色(accent)做1px边框，
        # 内层用卡片色(card)做内容区，避免亮/暗色模式下与其他窗口混淆
        # Floating window thin blue border: outer frame uses accent color as 1px border,
        # inner frame uses card color as content area, avoid blending with other windows
        self._border_color = c.accent
        self._window.configure(fg_color=c.accent)

        # 内层容器（卡面色，留出1px外边框效果）
        # Inner container (card color, leaving 1px border effect)
        self._inner_frame = ctk.CTkFrame(self._window, fg_color=c.card, corner_radius=0)
        self._inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # 使用 CustomTkinter 的 CTkLabel（放在内层容器上）
        # Use CTkLabel (placed on inner frame)
        self._status_label = ctk.CTkLabel(
            self._inner_frame, text=_("status.ready"), font=(get_font_family(), get_font_size(16), "bold"),
            text_color=c.text
        )
        self._status_label.pack(pady=10)

        screen_w = self._window.winfo_screenwidth()
        screen_h = self._window.winfo_screenheight()
        self._window.geometry(f"200x50+{(screen_w - 200) // 2}+{int(screen_h * 0.7)}")

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_dragging(self, event):
        x = self._window.winfo_x() + event.x - self._drag_data["x"]
        y = self._window.winfo_y() + event.y - self._drag_data["y"]
        self._window.geometry(f"+{x}+{y}")

    def set_status(self, status):
        self._status_label.configure(text=status)

    def apply_theme(self, colors):
        # 主题切换时刷新悬浮窗边框、背景和文字颜色
        # 用 try 防止窗口已销毁时报错
        # Refresh floating window border, bg and text colors on theme switch
        # Use try to avoid error if window already destroyed
        try:
            # 外层窗口用 accent 色做细边框
            # Outer window uses accent color as thin border
            self._window.configure(fg_color=colors.accent)
            # 内层容器用卡面色
            # Inner frame uses card color
            if hasattr(self, '_inner_frame'):
                self._inner_frame.configure(fg_color=colors.card)
            self._status_label.configure(text_color=colors.text)
        except Exception:
            pass

    def show(self):
        self._window.deiconify()

    def hide(self):
        self._window.withdraw()

    def destroy(self):
        self._window.destroy()


class MainWindow:
    # 主窗口类 - 使用 CustomTkinter 实现
    # 所有颜色统一�?config.json 读取
    
    def __init__(self, config=None):
        self._config = config
        if config:
            theme_str = config.get("theme", "dark")
            self._theme = THEME_LIGHT if theme_str == "light" else THEME_DARK
            self._floating_enabled = config.get("floating_enabled", True)
        else:
            self._theme = THEME_DARK
            self._floating_enabled = False
        
        # 设置 CustomTkinter 外观模式
        if self._theme == THEME_DARK:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 应用字体缩放（从配置读取，只缩放字体不缩放控件，避免整体缩放难看）
        # Apply font scaling (read from config, only scale fonts not widgets, avoid ugly overall scaling)
        font_scale = config.get("font_scale", 1.0) if config else 1.0
        set_font_scale(font_scale)

        # 使用 CustomTkinter 的 CTk
        self._root = ctk.CTk()
        self._root.title(_("app.title"))
        self._root.geometry("700x520")
        self._root.minsize(650, 450)

        self._recognized_text = ""
        self._running = False
        self._on_close_callback = None
        # 热键监听器的暂停/恢复回调（由 main.py 传入，用于设置页捕获热键时避免冲突）
        # Hotkey listener pause/resume callbacks (passed from main.py, avoid conflict when capturing)
        self._pause_hotkey = None
        self._resume_hotkey = None
        # 历史记录延迟加载：启动时不加载，首次切换到历史页面时才从文件读取
        # 这样减少启动时内存占用，用户大部分时间不用历史页面
        # Lazy load history: not loaded on startup, loaded on first switch to history page
        # Reduces startup memory usage, users rarely need history page
        self._history = None
        # 创建主题颜色实例，统一�?config.json 读取
        self.colors = ThemeColors(config)
        if config and config.get("theme", "dark") == "light":
            self.colors.apply_light()
        self.floating_window = None

        self._current_page = 0
        self._pages = []
        self._nav_buttons = []
        self._theme_btns = []
        self._theme_btn_containers = []
        self._title_labels = []

        self._setup_ui()
        self._apply_theme()
        self._update_theme_combo()
        if self._floating_enabled:
            self._root.after(100, self._init_floating_window_hidden)

    def load_theme_from_config(self, config: dict):
        self._config = config
        theme_str = config.get("theme", "dark")
        if theme_str == "light":
            self._theme = THEME_LIGHT
        else:
            self._theme = THEME_DARK
        self._floating_enabled = config.get("floating_enabled", True)
        # 确保 floating_enabled 字段存在（业务逻辑已抽至 AppController）
        # Ensure floating_enabled field exists (business logic moved to AppController)
        AppController.ensure_floating_default(self._config)
        self._apply_theme()
        self._update_theme_combo()
        self._update_floating_switch()
        self._update_autostart_switch()

    def _init_floating_window(self):
        self.floating_window = FloatingWindow(self._root)
        self.floating_window.show()

    def _init_floating_window_hidden(self):
        self.floating_window = FloatingWindow(self._root)
        self.floating_window.hide()

    def _update_floating_switch(self):
        # 更新悬浮窗开关状态（从配置加载后同步界面）
        if hasattr(self, '_floating_switch'):
            if self._floating_enabled:
                self._floating_switch.select()
            else:
                self._floating_switch.deselect()
            # 更新开关旁的文字
            self._floating_switch.configure(text=_("button.enabled") if self._floating_enabled else _("button.disabled"))

    def _setup_ui(self):
        # 使用 CustomTkinter �?grid 布局
        self._root.grid_columnconfigure(1, weight=1)
        self._root.grid_rowconfigure(0, weight=1)

        # 使用 CustomTkinter �?CTkFrame
        sidebar = ctk.CTkFrame(self._root, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar = sidebar

        # 使用 CustomTkinter �?CTkLabel
        self._logo_label = ctk.CTkLabel(
            sidebar, text=_("app.title"), font=(get_font_family(), get_font_size(21), "bold"),
            text_color=self.colors.logo_color
        )
        self._logo_label.pack(fill="x", pady=(20, 10), padx=0)

        nav_items = [("nav.home", 0), ("nav.log", 1), ("nav.history", 2), ("nav.ai", 3), ("nav.toolbox", 4), ("nav.settings", 5)]
        for name_key, idx in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=_(name_key), font=(get_font_family(), get_font_size(17)),
                fg_color="transparent",
                text_color=self.colors.text_secondary,
                hover_color=self.colors.hover,
                command=lambda i=idx: self._switch_tab(i),
                corner_radius=0,
                border_width=0
            )
            btn.pack(fill="x", padx=0, pady=2)
            self._nav_buttons.append(btn)

        self._nav_buttons[0].configure(fg_color=self.colors.active, text_color=self.colors.text)

        content = ctk.CTkFrame(self._root, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        self._content = content

        self._page_container = ctk.CTkFrame(content, corner_radius=0)
        self._page_container.pack(fill="both", expand=True, padx=0, pady=0)

        # 页面懒加载：启动时只创建首页，其他页面首次切换时才创建
        # 这样能减少启动时的控件创建开销，加快首次显示
        # Lazy loading: only create home page on startup, others created on first switch
        # Reduces startup widget creation overhead, speeds up first display
        # home(0) 控件被外部频繁访问，必须立即创建
        # log(1) 和 ai(3) 在 start()/load_settings() 中提前触发创建
        # history(2)/toolbox(4)/settings(5) 真正懒加载，切换时才创建
        self._pages = [None] * 6
        self._pages[0] = self._create_home_page()

        self._switch_tab(0)

    def _ensure_page_created(self, index):
        # 确保指定页面已创建（懒加载触发）
        # index: 页面索引（0-5）
        # Ensure specified page is created (lazy load trigger)
        # index: page index (0-5)
        if self._pages[index] is not None:
            return
        # 记录创建前的 title_labels 数量，用于只刷新新增的标签（避免全量 _apply_theme 重复刷新已存在控件）
        # Record title_labels count before creation, to only refresh newly added labels
        # (avoids full _apply_theme re-refreshing existing controls)
        prev_title_count = len(self._title_labels)
        # 根据索引调用对应的创建方法
        # Call corresponding create method based on index
        if index == 1:
            self._pages[1] = self._create_log_page()
        elif index == 2:
            self._pages[2] = self._create_history_page()
        elif index == 3:
            self._pages[3] = self._create_ai_page()
        elif index == 4:
            self._pages[4] = self._create_toolbox_page()
        elif index == 5:
            self._pages[5] = self._create_settings_page()
        # 只刷新新页面创建时新增的 title_labels 颜色（轻量级，不全量刷新所有控件）
        # Only refresh title_labels colors added during new page creation (lightweight, no full refresh)
        c = self.colors
        for label in self._title_labels[prev_title_count:]:
            label.configure(text_color=c.text)

    def _create_home_page(self):
        page = ctk.CTkScrollableFrame(self._page_container, corner_radius=0)

        self._status_label = ctk.CTkLabel(
            page, text=_("status.ready"), font=(get_font_family(), get_font_size(19)),
            text_color=self.colors.text
        )
        self._status_label.pack(anchor="w", padx=30, pady=(20, 5))

        # 主页提示文字：动态替换为当前快捷键
        # 翻译里写死 Ctrl+Alt，但快捷键可自定义，需替换为实际配置值
        # Home hint: dynamically replace with current hotkey
        # Translation hardcodes Ctrl+Alt, but hotkey is customizable, replace with actual config value
        hotkey_raw = self._config.get("hotkey_combo", "ctrl+alt") if self._config else "ctrl+alt"
        # 美化显示：每段首字母大写（ctrl+alt → Ctrl+Alt，ctrl+shift+v → Ctrl+Shift+V）
        # Beautify display: capitalize each segment
        hotkey_display = "+".join(p.capitalize() for p in hotkey_raw.split("+"))
        # 用当前快捷键替换翻译中的固定 Ctrl+Alt 字样
        # Replace fixed Ctrl+Alt in translation with current hotkey
        hint_text = _("home.hint").replace("Ctrl+Alt", hotkey_display)
        hint = ctk.CTkLabel(
            page, text=hint_text,
            font=(get_font_family(), get_font_size(14)), text_color=self.colors.text_secondary
        )
        self._title_labels.append(hint)
        hint.pack(anchor="w", padx=30, pady=(0, 15))

        self._home_title_frame = ctk.CTkFrame(page, corner_radius=0)
        self._home_title_frame.pack(fill="x", padx=30, pady=(0, 10))

        text_title = ctk.CTkLabel(
            self._home_title_frame, text=_("home.result_title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(text_title)
        text_title.pack(side="left")

        copy_btn = ctk.CTkButton(
            self._home_title_frame, text=_("button.copy"), font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=self._copy_and_save,
            corner_radius=6,
            height=30
        )
        copy_btn.pack(side="right")

        # 使用 CustomTkinter �?CTkTextbox
        self._text_edit = ctk.CTkTextbox(
            page, font=(get_font_family(), get_font_size(17)),
            fg_color=self.colors.card, text_color=self.colors.text,
            corner_radius=6,
            height=300
        )
        self._text_edit.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        return page

    def _create_settings_page(self):
        # 创建系统设置�?
        # 使用 CustomTkinter 组件
        # 所有颜色统一�?config.json 读取
        page = ctk.CTkScrollableFrame(self._page_container, corner_radius=0)

        settings_title = ctk.CTkLabel(
            page, text=_("settings.title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(settings_title)
        settings_title.pack(anchor="w", padx=30, pady=(20, 20))

        theme_label = ctk.CTkLabel(
            page, text=_("settings.theme"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(theme_label)
        theme_label.pack(anchor="w", padx=30, pady=(0, 10))

        # 创建主题选择下拉框（使用 ttk.Combobox，Windows 原生箭头样式正常）
        # ttk.Combobox 的箭头是系统原生样式，比 CTkOptionMenu 的箭头美观
        # Create theme dropdown (using ttk.Combobox, native Windows arrow style)
        self._theme_var = tk.StringVar()
        theme_options = [_("settings.theme_light"), _("settings.theme_dark")]
        current_theme_str = "light" if self._theme == THEME_LIGHT else "dark"
        current_theme_display = _("settings.theme_light") if current_theme_str == "light" else _("settings.theme_dark")
        self._theme_var.set(current_theme_display)

        # 配置 ttk.Style（让 Combobox 颜色随应用主题切换，clam 主题支持完整颜色定制）
        # Configure ttk.Style (combobox colors follow app theme, clam theme supports full color customization)
        self._combo_style = ttk.Style()
        self._combo_style.theme_use("clam")
        # 主样式：fieldbackground=输入框背景，background=箭头按钮背景
        # Main style: fieldbackground=input bg, background=arrow button bg
        self._combo_style.configure("AICombo.TCombobox",
            fieldbackground=self.colors.card,
            background=self.colors.card,
            foreground=self.colors.text,
            bordercolor=self.colors.border,
            arrowcolor=self.colors.text,
            arrowsize=24,
            font=(get_font_family(), get_font_size(15)),
            padding=8,
            # 下拉列表背景色（防止暗色模式下拉列表显示为刺眼的白色）
            # Dropdown list background (prevents jarring white dropdown in dark mode)
            selectbackground=self.colors.active,
            selectforeground=self.colors.text
        )
        # 通过 map 配置下拉弹出列表的颜色（clam 主题下必须用 map 才能影响下拉列表）
        # Configure dropdown popup colors via map (clam theme requires map to affect dropdown list)
        self._combo_style.map(
            "AICombo.TCombobox",
            selectbackground=[("readonly", self.colors.active)],
            selectforeground=[("readonly", self.colors.text)],
            fieldbackground=[("readonly", self.colors.card)],
            foreground=[("readonly", self.colors.text)]
        )

        self._theme_combo = ttk.Combobox(
            page, textvariable=self._theme_var, values=theme_options,
            state="readonly", style="AICombo.TCombobox"
        )
        # ttk.Combobox 用 <<ComboboxSelected>> 事件绑定回调（替代 CTkOptionMenu 的 command 参数）
        # ttk.Combobox uses <<ComboboxSelected>> event for callback (replaces CTkOptionMenu's command)
        self._theme_combo.bind("<<ComboboxSelected>>", self._on_theme_changed)
        # 使用 anchor="w" + width 限制下拉框宽度（避免 fill="x" 撑满整行显得过长）
        # Use anchor="w" + width to limit dropdown width (avoid fill="x" stretching full row)
        self._theme_combo.configure(width=22)
        self._theme_combo.pack(anchor="w", padx=30, pady=(0, 20))

        # 创建"界面语言"标签（在主题按钮下方�?
        language_label = ctk.CTkLabel(
            page, text=_("settings.language"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(language_label)
        language_label.pack(anchor="w", padx=30, pady=(15, 5))

        # 创建语言选择下拉框（使用 ttk.Combobox，与主题下拉框相同样式）
        # Create language dropdown (using ttk.Combobox, same style as theme dropdown)
        self._language_var = tk.StringVar()
        supported_langs = get_supported_languages()
        lang_display_names = [get_language_name(code) for code in supported_langs]
        current_lang_code = get_current_language()
        if current_lang_code in supported_langs:
            current_index = supported_langs.index(current_lang_code)
            self._language_var.set(lang_display_names[current_index])
        else:
            self._language_var.set(lang_display_names[0])

        # 复用 AICombo.TCombobox 样式（与主题下拉框一致）
        # Reuse AICombo.TCombobox style (same as theme dropdown)
        self._language_combo = ttk.Combobox(
            page, textvariable=self._language_var, values=lang_display_names,
            state="readonly", style="AICombo.TCombobox"
        )
        self._language_combo.bind("<<ComboboxSelected>>", self._on_language_changed_option)
        # 使用 anchor="w" + width 限制下拉框宽度（与主题下拉框一致，不撑满整行）
        # Use anchor="w" + width to limit width (same as theme dropdown, not stretch full row)
        self._language_combo.configure(width=22)
        self._language_combo.pack(anchor="w", padx=30, pady=(0, 20))

        # 创建"字体大小"标签
        # Create "Font Size" label
        font_size_label = ctk.CTkLabel(
            page, text=_("settings.font_size"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(font_size_label)
        font_size_label.pack(anchor="w", padx=30, pady=(15, 10))

        # 字体大小调节：Label 显示 + 上下箭头按钮（像 Word 调字体大小那样）
        # 范围 8-15，步进 1，只缩放字体不缩放控件，重启后生效
        # 纯 Label 显示，避免输入框让用户误以为要输入
        # Font size: Label display + up/down arrow buttons (like Word font size)
        # Level 8-15 (step 1), only scale fonts not widgets, takes effect after restart
        # Pure Label display, avoid input box misleading users
        # 字号等级：10 为基准（font_scale=1.0），调小 9/8，调大 11/12/13，范围 8-15
        # Font size level: 10 is base (font_scale=1.0), smaller 9/8, larger 11/12/13, range 8-15
        font_size_level = int(round(self._config.get("font_scale", 1.0) * 10)) if self._config else 10
        # 显示字号等级数字（如 "10"）
        # Display font size level number (e.g. "10")
        self._font_scale_var = tk.StringVar(value=str(font_size_level))
        # 横向布局容器：显示框 + 上下箭头按钮
        # Horizontal layout container: display + up/down arrow buttons
        font_size_frame = ctk.CTkFrame(page, fg_color="transparent")
        font_size_frame.pack(anchor="w", padx=30, pady=(0, 5))
        # 显示当前字体大小百分比（纯显示，不可输入）
        # Display current font size percentage (display only, no input)
        self._font_scale_label = ctk.CTkLabel(
            font_size_frame, textvariable=self._font_scale_var,
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.card, text_color=self.colors.text,
            corner_radius=6, height=32, width=70, justify="center"
        )
        self._font_scale_label.pack(side="left", padx=(0, 8))
        # 上箭头按钮：增大字体（步进 1），尺寸稍小一号
        # 存为实例属性以便主题切换时刷新颜色
        # 次级按钮统一用 hover 底（亮色浅灰层次清晰，暗色与 card 几乎一致）
        # Up arrow button: increase font (step 1), slightly smaller size
        # Store as instance attribute for theme switch color refresh
        # Secondary buttons use hover bg (light: clear gray layer, dark: near-identical to card)
        self._font_up_btn = ctk.CTkButton(
            font_size_frame, text="▲", font=(get_font_family(), get_font_size(13)),
            fg_color=self.colors.hover, text_color=self.colors.text,
            hover_color=self.colors.active,
            command=lambda: self._on_font_scale_changed(1),
            corner_radius=6, height=32, width=34
        )
        self._font_up_btn.pack(side="left", padx=(0, 4))
        # 下箭头按钮：减小字体（步进 1），尺寸稍小一号
        # 存为实例属性以便主题切换时刷新颜色
        # 次级按钮统一用 hover 底
        # Down arrow button: decrease font (step 1), slightly smaller size
        # Store as instance attribute for theme switch color refresh
        # Secondary buttons use hover bg
        self._font_down_btn = ctk.CTkButton(
            font_size_frame, text="▼", font=(get_font_family(), get_font_size(13)),
            fg_color=self.colors.hover, text_color=self.colors.text,
            hover_color=self.colors.active,
            command=lambda: self._on_font_scale_changed(-1),
            corner_radius=6, height=32, width=34
        )
        self._font_down_btn.pack(side="left")

        # 提示文字：用上下箭头调节，重启后生效
        # Hint: use up/down arrows, takes effect after restart
        font_size_hint = ctk.CTkLabel(
            page, text=_("settings.font_size_hint"),
            font=(get_font_family(), get_font_size(12)), text_color=self.colors.text_secondary
        )
        self._title_labels.append(font_size_hint)
        font_size_hint.pack(anchor="w", padx=30, pady=(0, 20))

        # 创建"开机自启动"标签
        autostart_label = ctk.CTkLabel(
            page, text=_("settings.autostart"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(autostart_label)
        autostart_label.pack(anchor="w", padx=30, pady=(0, 10))

        # 创建开机自启动开关（使用 CTkSwitch 替代下拉菜单，更直观）
        autostart_enabled = self._config.get("autostart", False) if self._config else False
        self._autostart_switch = ctk.CTkCheckBox(
            page,
            text=_("button.enabled") if autostart_enabled else _("button.disabled"),
            font=(get_font_family(), get_font_size(17)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            corner_radius=4,
            command=self._on_autostart_changed
        )
        # 设置开关初始状态（选中或取消选中）
        if autostart_enabled:
            self._autostart_switch.select()
        self._autostart_switch.pack(anchor="w", padx=30, pady=(0, 20))

        # 创建"快捷键"标签
        # Create "Hotkey" label
        hotkey_label = ctk.CTkLabel(
            page, text=_("settings.hotkey"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(hotkey_label)
        hotkey_label.pack(anchor="w", padx=30, pady=(0, 10))

        # 热键显示框 + 修改按钮（横向布局）
        # Hotkey display + change button (horizontal layout)
        hotkey_frame = ctk.CTkFrame(page, fg_color="transparent")
        hotkey_frame.pack(anchor="w", padx=30, pady=(0, 5))
        current_hotkey = self._config.get("hotkey_combo", "ctrl+alt") if self._config else "ctrl+alt"
        self._hotkey_var = tk.StringVar(value=current_hotkey)
        # 当前热键显示（纯 Label 显示，不可输入，只能通过"修改"按钮设置）
        # 避免使用输入框让用户误以为此处需要键入文字
        # Current hotkey display (Label only, no input, set only via "change" button)
        # Avoid input box misleading users into thinking they need to type here
        self._hotkey_entry = ctk.CTkLabel(
            hotkey_frame, textvariable=self._hotkey_var,
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.card, text_color=self.colors.text,
            corner_radius=6, height=40, width=180, justify="center"
        )
        self._hotkey_entry.pack(side="left", padx=(0, 10))
        # 修改按钮：点击后弹出独立窗口捕获按键
        # Change button: click to open standalone capture dialog
        change_btn = ctk.CTkButton(
            hotkey_frame, text=_("settings.hotkey_change"), font=(get_font_family(), get_font_size(14)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=self._open_hotkey_dialog,
            corner_radius=6, height=40, width=80
        )
        change_btn.pack(side="left")

        # 提示文字（外部 Label，不写入输入框）
        # Hint text (external Label, not written into entry)
        hotkey_hint = ctk.CTkLabel(
            page, text=_("settings.hotkey_hint"),
            font=(get_font_family(), get_font_size(12)), text_color=self.colors.text_secondary
        )
        self._title_labels.append(hotkey_hint)
        hotkey_hint.pack(anchor="w", padx=30, pady=(0, 20))

        # 创建"悬浮窗模�?标签
        floating_label = ctk.CTkLabel(
            page, text=_("settings.floating"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(floating_label)
        floating_label.pack(anchor="w", padx=30, pady=(0, 10))

        # 创建悬浮窗模式开关（使用 CTkSwitch 替代下拉菜单，更直观）
        self._floating_switch = ctk.CTkCheckBox(
            page,
            text=_("button.enabled") if self._floating_enabled else _("button.disabled"),
            font=(get_font_family(), get_font_size(17)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            corner_radius=4,
            command=self._on_floating_changed
        )
        # 设置开关初始状态
        if self._floating_enabled:
            self._floating_switch.select()
        self._floating_switch.pack(anchor="w", padx=30, pady=(0, 15))

        return page

    def _on_language_changed_option(self, event=None):
        # 语言选择改变事件处理（ttk.Combobox 版本，GUI 部分）
        # ttk.Combobox 的 <<ComboboxSelected>> 事件传 event 参数，用 var.get() 获取选中值
        # 配置保存逻辑已抽至 AppController.change_language()
        # Language change event handler (ttk.Combobox version, GUI part)
        # ttk.Combobox's <<ComboboxSelected>> event passes event param, use var.get() for selected value
        # Config save logic moved to AppController.change_language()
        selected_display_name = self._language_var.get()
        supported_langs = get_supported_languages()
        lang_display_names = [get_language_name(code) for code in supported_langs]
        if selected_display_name in lang_display_names:
            selected_index = lang_display_names.index(selected_display_name)
            selected_lang_code = supported_langs[selected_index]
            # 切换当前界面语言
            set_language(selected_lang_code)
            # 调用应用控制器：更新配置字典并保存到文件
            AppController.change_language(self._config, selected_lang_code)
            # 刷新界面文字
            self._refresh_ui_texts()
            # 提示用户需要重启生效
            messagebox.showinfo(_("settings.language"), _("settings.restart_hint"))

    def _on_theme_changed(self, event=None):
        # 主题选择改变事件处理（ttk.Combobox 版本）
        # ttk.Combobox 的 <<ComboboxSelected>> 事件传 event 参数，用 var.get() 获取选中值
        # Theme change event handler (ttk.Combobox version)
        selected_display_name = self._theme_var.get()
        if selected_display_name == _("settings.theme_light"):
            self._set_theme(THEME_LIGHT)
        else:
            self._set_theme(THEME_DARK)

    def _on_font_scale_changed(self, delta: int):
        # 字体大小调节回调：点击上下箭头按钮增减字号等级并保存到配置
        # 字号等级：10=1.0 基准，8=0.8 最小，15=1.5 最大，步进 1
        # 只缩放字体（通过 get_font_size 全局系数），不缩放控件和窗口
        # 重启后生效（避免遍历所有控件重新设置 font）
        # delta: 增量（+1 增大，-1 减小）
        # Font size change callback: click up/down arrow to change level and save
        # Level: 10=1.0 base, 8=0.8 min, 15=1.5 max, step 1
        # Only scale fonts (via get_font_size global factor), not widgets and window
        # Takes effect after restart (avoid traversing all widgets to reset font)
        # delta: increment (+1 increase, -1 decrease)
        if not self._config:
            return
        try:
            # 读取当前字号等级（数字字符串转整数）
            # Read current font size level (numeric string to int)
            current = int(self._font_scale_var.get().strip())
            # 加上增量并限制范围 8-15
            # Add delta and clamp to 8-15
            level = max(8, min(15, current + delta))
            # 更新 Label 显示
            # Update Label display
            self._font_scale_var.set(str(level))
            # 转为缩放系数（10 → 1.0，13 → 1.3）
            # Convert to scale factor (10 → 1.0, 13 → 1.3)
            scale = level / 10.0
            # 保存到配置文件（重启后由 set_font_scale 应用）
            # Save to config (applied by set_font_scale on restart)
            AppController._update_and_save(self._config, "font_scale", scale, "字体大小")
            # 提示用户需要重启生效
            # Prompt user that restart is needed
            self._status_label.configure(text=_("settings.font_size_restart_needed"))
        except (ValueError, TypeError):
            # 数值异常时忽略
            # Ignore on numeric error
            pass

    def _on_autostart_changed(self):
        # 开机自启动开关切换事件处理（GUI 部分）
        # 业务逻辑（配置保存 + 注册表注册）已抽至 AppController.set_autostart_enabled()
        if not self._config:
            return
        # 从开关读取当前状态（True=启用，False=禁用）
        autostart_enabled = self._autostart_switch.get()
        # 更新开关旁的文字显示
        self._autostart_switch.configure(text=_("button.enabled") if autostart_enabled else _("button.disabled"))
        try:
            # 调用应用控制器：保存配置 + 实际注册/取消注册开机启动
            AppController.set_autostart_enabled(self._config, autostart_enabled)
            # 更新状态栏提示
            self._status_label.configure(text=_("status.autostart_enabled") if autostart_enabled else _("status.autostart_disabled"))
        except Exception as e:
            self._status_label.configure(text=_("settings.save_error") + ": %s" % str(e))

    def _open_hotkey_dialog(self):
        # 打开热键捕获弹窗：点击"修改"按钮后弹出独立窗口捕获按键
        # 弹窗打开时暂停全局热键监听（避免捕获按键时触发录音），关闭时恢复
        # 支持单键/双键/三键组合，用 GetAsyncKeyState 实时查询修饰键状态（比 event.state 可靠）
        # Open hotkey capture dialog: standalone window to capture keypress
        # Pause global hotkey listener while open (avoid triggering recording), resume on close
        # Supports 1-3 key combo, uses GetAsyncKeyState for reliable modifier state
        if not self._config:
            return
        # 暂停全局热键监听，弹窗期间不会触发录音
        # Pause global hotkey listener, no recording trigger during dialog
        if self._pause_hotkey:
            self._pause_hotkey()
        # 用 tk.Toplevel 创建弹窗（比 CTkToplevel 焦点更可靠，grab_set 能拦截所有按键）
        # Use tk.Toplevel (more reliable focus than CTkToplevel, grab_set catches all keys)
        dialog = tk.Toplevel(self._root)
        dialog.title(_("settings.hotkey_dialog_title"))
        dialog.geometry("440x280")
        dialog.transient(self._root)
        dialog.resizable(False, False)
        # 背景色随主题（用 tk 控件需手动配颜色）
        # Background follows theme (tk widgets need manual color)
        bg = self.colors.content
        dialog.configure(bg=bg)
        # 提示文字 Label
        # Hint label
        tk.Label(
            dialog, text=_("settings.hotkey_dialog_hint"),
            font=(get_font_family(), get_font_size(12)), fg=self.colors.text_secondary, bg=bg
        ).pack(pady=(25, 8))
        # 实时显示已捕获的键（大字体居中）
        # Real-time display of captured keys (large font, centered)
        display_var = tk.StringVar(value=_("settings.hotkey_waiting"))
        tk.Label(
            dialog, textvariable=display_var,
            font=(get_font_family(), get_font_size(22), "bold"),
            fg=self.colors.accent, bg=bg
        ).pack(pady=8)
        # 第二行提示：按下非修饰键完成捕获
        # Second hint: press non-modifier key to finish capture
        tk.Label(
            dialog, text=_("settings.hotkey_dialog_hint2"),
            font=(get_font_family(), get_font_size(11)), fg=self.colors.text_secondary, bg=bg
        ).pack(pady=(0, 5))

        # 已捕获的键名列表（最多 3 个）
        # Captured key name list (max 3)
        captured = []
        # 是否已捕获完成（按下非修饰键后置 True）
        # Whether capture finished (True after pressing non-modifier key)
        finished = [False]
        # 获取 user32 引用查询修饰键实时状态
        # Get user32 ref to query modifier state in real time
        import ctypes
        user32 = ctypes.windll.user32

        def _query_modifiers():
            # 用 GetAsyncKeyState 查询当前按下的修饰键（0x8000 最高位=按下）
            # Query pressed modifiers via GetAsyncKeyState (0x8000 high bit = pressed)
            mods = []
            if user32.GetAsyncKeyState(0x11) & 0x8000:  # Ctrl
                mods.append("ctrl")
            if user32.GetAsyncKeyState(0x12) & 0x8000:  # Alt
                mods.append("alt")
            if user32.GetAsyncKeyState(0x10) & 0x8000:  # Shift
                mods.append("shift")
            if user32.GetAsyncKeyState(0x5B) & 0x8000:  # 左 Win
                mods.append("win")
            return mods

        def _on_dialog_key_press(event):
            # 弹窗按键事件：捕获用户按下的键
            # Dialog key event: capture user keypress
            # 已完成则不再处理
            # Skip if already finished
            if finished[0]:
                return
            keysym = event.keysym.lower()
            # 实时查询当前所有修饰键状态
            # Query current modifier state in real time
            mods = _query_modifiers()
            # 如果按下的是修饰键本身，只更新显示当前修饰键组合（等待用户继续按非修饰键）
            # If pressed key is a modifier itself, only update display (wait for non-modifier key)
            if keysym in ("control_l", "control_r", "alt_l", "alt_r",
                          "shift_l", "shift_r", "win_l", "win_r", "super_l", "super_r"):
                if mods:
                    captured.clear()
                    # 修饰键最多取 3 个
                    # Take at most 3 modifiers
                    captured.extend(mods[:3])
                    display_var.set("+".join(captured))
                return
            # 非修饰键：组合 = 修饰键 + 当前键
            # Non-modifier key: combo = modifiers + current key
            key_name = self._keysym_to_name(keysym)
            # 不支持的键直接忽略
            # Ignore unsupported keys
            if not key_name:
                return
            combo = mods + [key_name]
            captured.clear()
            # 最多 3 个键
            # At most 3 keys
            captured.extend(combo[:3])
            display_var.set("+".join(captured))
            # 标记完成，用户可点确认保存
            # Mark finished, user can click confirm to save
            finished[0] = True

        def _on_confirm():
            # 确认按钮：保存捕获的热键组合
            # Confirm button: save captured hotkey combo
            if captured:
                combo_str = "+".join(captured[:3])
                # 验证所有键名都在 VK_MAP 中
                # Validate all key names in VK_MAP
                from .hotkey import VK_MAP
                combo_parts = combo_str.split("+")
                valid = all(p in VK_MAP for p in combo_parts)
                if valid and 1 <= len(combo_parts) <= 3:
                    # 保存到配置文件
                    # Save to config file
                    AppController._update_and_save(self._config, "hotkey_combo", combo_str, "快捷键")
                    # 更新主界面显示
                    # Update main UI display
                    self._hotkey_var.set(combo_str)
                    # 提示重启后生效
                    # Prompt restart needed
                    self._status_label.configure(text=_("settings.hotkey_restart_needed"))
            # 恢复全局监听并关闭弹窗
            # Resume global listener and close dialog
            if self._resume_hotkey:
                self._resume_hotkey()
            dialog.destroy()

        def _on_cancel():
            # 取消按钮：不保存，恢复监听并关闭
            # Cancel button: don't save, resume listener and close
            if self._resume_hotkey:
                self._resume_hotkey()
            dialog.destroy()

        # 绑定弹窗按键事件（弹窗内任意位置按键都能捕获）
        # Bind dialog key event (any key in dialog is captured)
        dialog.bind("<KeyPress>", _on_dialog_key_press)
        dialog.focus_set()
        dialog.grab_set()
        # 按钮区（确认/取消）
        # Button frame (confirm/cancel)
        btn_frame = tk.Frame(dialog, bg=bg)
        btn_frame.pack(pady=18)
        tk.Button(
            btn_frame, text=_("button.confirm"), command=_on_confirm,
            font=(get_font_family(), get_font_size(12)), width=10
        ).pack(side="left", padx=12)
        tk.Button(
            btn_frame, text=_("button.cancel"), command=_on_cancel,
            font=(get_font_family(), get_font_size(12)), width=10
        ).pack(side="left", padx=12)
        # 关闭窗口（点 X）等同于取消
        # Closing window (click X) equals cancel
        dialog.protocol("WM_DELETE_WINDOW", _on_cancel)

    @staticmethod
    def _keysym_to_name(keysym: str) -> str:
        # 将 Tkinter keysym 转换为 VK_MAP 中的键名
        # Convert Tkinter keysym to key name in VK_MAP
        # 字母键 a-z
        # Letter keys a-z
        if len(keysym) == 1 and keysym.isalpha():
            return keysym
        # 数字键 0-9
        # Number keys 0-9
        if len(keysym) == 1 and keysym.isdigit():
            return keysym
        # 功能键 f1-f12
        # Function keys f1-f12
        if keysym.startswith("f") and keysym[1:].isdigit():
            return keysym
        # 空格
        # Space
        if keysym == "space":
            return "space"
        # 回车
        # Enter
        if keysym == "return":
            return "enter"
        # 不支持的键返回空
        # Unsupported key returns empty
        return ""

    def _set_autostart(self, enabled: bool):
        # 设置或取消开机自启动（业务逻辑已移至 app_controller.py）
        # 三级方案：注册表 Run 键 > 快捷方式 .lnk > .bat 脚本
        # enabled: True=启用自启动，False=禁用自启动
        AppController.set_autostart(enabled)

    def _on_floating_changed(self):
        # 悬浮窗开关切换事件处理
        # 从开关读取当前状态
        self._floating_enabled = self._floating_switch.get()
        # 更新开关旁的文字显示
        self._floating_switch.configure(text=_("button.enabled") if self._floating_enabled else _("button.disabled"))
        if self._floating_enabled:
            # 启用悬浮窗：创建并显示
            if not self.floating_window:
                self.floating_window = FloatingWindow(self._root)
            self.floating_window.show()
        else:
            # 禁用悬浮窗：隐藏
            if self.floating_window:
                self.floating_window.hide()
        self._save_floating_to_config()

    def _save_toolbox_config(self, key: str, value):
        # 保存工具箱配置项到配置文件（业务逻辑已移至 app_controller.py）
        # key: 配置键名
        # value: 配置值
        AppController.save_toolbox_config(self._config, key, value)

    def _on_punct_changed(self):
        # 去除末尾标点开关切换事件
        enabled = self._punct_switch.get()
        self._save_toolbox_config("remove_trailing_punct", enabled)

    def _on_itn_changed(self):
        # ITN数字转换开关切换事件
        enabled = self._itn_switch.get()
        self._save_toolbox_config("itn_enabled", enabled)

    def _on_hot_changed(self):
        # 热词替换开关切换事件
        enabled = self._hot_switch.get()
        self._save_toolbox_config("hot_enabled", enabled)

    def _on_threshold_changed(self, value):
        # 热词匹配阈值滑块改变事件
        # value: 滑块当前值
        threshold = round(float(value), 2)
        # 更新阈值显示标签
        threshold_text = _("toolbox.threshold_format").replace("{value}", f"{threshold:.2f}")
        if hasattr(self, '_threshold_label'):
            self._threshold_label.configure(text=threshold_text)
        self._save_toolbox_config("hot_threshold", threshold)

    def _on_rule_changed(self):
        # 正则替换开关切换事件
        enabled = self._rule_switch.get()
        self._save_toolbox_config("hot_rule_enabled", enabled)

    def show_api_config_dialog(self, title_key: str, config_prefix: str):
        # 统一 API 配置弹窗（ASR 和 LLM 共用同一个界面，可复用）
        # title_key: 弹窗标题的翻译键（"ai.config_asr" 或 "ai.config_llm"）
        # config_prefix: 配置键前缀
        #   "" -> 保存到 base_url/api_key/model（ASR 配置）
        #   "llm_" -> 保存到 llm_base_url/llm_api_key/llm_model（LLM 配置）
        # 每次打开时显示已保存的内容，方便修改；保存后写入配置并落盘
        # LLM 弹窗额外包含"与 ASR 共用 API key 和 API 地址"开关，开启时地址和密钥灰色显示 ASR 值
        # Unified API config dialog (shared by ASR and LLM, reusable)
        # LLM dialog additionally contains "Share API key & URL with ASR" switch

        # 拼接三个配置键名（前缀 + 字段名）
        # Build three config key names (prefix + field name)
        url_key = config_prefix + "base_url"
        apikey_key = config_prefix + "api_key"
        model_key = config_prefix + "model"
        # 是否为 LLM 弹窗（决定是否显示共用开关）
        # Whether this is LLM dialog (determines whether to show share switch)
        is_llm = (config_prefix == "llm_")

        # 创建模态弹窗（transient 绑定主窗，grab_set 抓取焦点实现模态）
        # Create modal dialog (transient binds to main window, grab_set captures focus for modality)
        dialog = ctk.CTkToplevel(self._root)
        dialog.title(_(title_key))
        dialog.geometry("480x520")
        dialog.transient(self._root)
        dialog.grab_set()

        # ========== LLM 专属：与 ASR 共用开关 ==========
        # LLM only: share with ASR switch
        if is_llm:
            share_frame = ctk.CTkFrame(dialog, corner_radius=0, fg_color="transparent")
            share_frame.pack(fill="x", padx=20, pady=(15, 5))
            # 从配置读取是否共用，默认共用（省去重复输入）
            # Read share flag from config, default True (avoid duplicate input)
            llm_share = self._config.get("llm_share_asr", True) if self._config else True
            share_var = tk.BooleanVar(value=llm_share)
            share_checkbox = ctk.CTkCheckBox(
                share_frame, text=_("ai.llm_share_asr"), font=(get_font_family(), get_font_size(14)),
                variable=share_var,
                fg_color=self.colors.accent, border_color=self.colors.text_secondary,
                checkmark_color="white", hover_color=self.colors.hover,
                checkbox_width=22, checkbox_height=22
            )
            share_checkbox.pack(anchor="w")

        # ========== API 地址 ==========
        url_label = ctk.CTkLabel(
            dialog, text=_("ai.api_url"), font=(get_font_family(), get_font_size(15), "bold"),
            text_color=self.colors.text
        )
        url_label.pack(anchor="w", padx=20, pady=(10, 5))

        url_edit = ctk.CTkEntry(
            dialog, font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.card, text_color=self.colors.text,
            placeholder_text_color=self.colors.text_secondary,
            corner_radius=6, height=36,
            border_width=2, border_color=self.colors.border
        )
        url_edit.pack(fill="x", padx=20, pady=(0, 2))

        # 地址提示（不要以斜杠结尾，避免拼接路径出错）
        # URL hint (do not end with slash, avoid path join errors)
        url_hint = ctk.CTkLabel(
            dialog, text=_("ai.url_hint"), font=(get_font_family(), get_font_size(12)),
            text_color=self.colors.text_secondary
        )
        url_hint.pack(anchor="w", padx=20, pady=(0, 10))

        # ========== API 密钥 ==========
        key_label = ctk.CTkLabel(
            dialog, text=_("ai.api_key"), font=(get_font_family(), get_font_size(15), "bold"),
            text_color=self.colors.text
        )
        key_label.pack(anchor="w", padx=20, pady=(0, 5))

        key_edit = ctk.CTkEntry(
            dialog, font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.card, text_color=self.colors.text,
            placeholder_text_color=self.colors.text_secondary,
            corner_radius=6, height=36,
            border_width=2, border_color=self.colors.border,
            show="*"
        )
        key_edit.pack(fill="x", padx=20, pady=(0, 15))

        # ========== 模型名称 ==========
        model_label = ctk.CTkLabel(
            dialog, text=_("ai.model_name"), font=(get_font_family(), get_font_size(15), "bold"),
            text_color=self.colors.text
        )
        model_label.pack(anchor="w", padx=20, pady=(0, 5))

        model_edit = ctk.CTkEntry(
            dialog, font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.card, text_color=self.colors.text,
            placeholder_text_color=self.colors.text_secondary,
            corner_radius=6, height=36,
            border_width=2, border_color=self.colors.border
        )
        model_edit.pack(fill="x", padx=20, pady=(0, 20))

        # 根据共用状态回填字段值并设置可编辑状态
        # Fill field values and set editable state based on share state
        def _refresh_fields():
            # 根据共用开关状态读取对应值并设置字段可编辑性
            # Read values and set field editability based on share switch state
            if is_llm and share_var.get():
                # LLM 共用：地址和密钥从 ASR 读取（灰色不可改），模型从 LLM 读取（可改）
                # LLM sharing: URL and key from ASR (read-only), model from LLM (editable)
                url_val = self._config.get("base_url", "") if self._config else ""
                key_val = self._config.get("api_key", "") if self._config else ""
                model_val = self._config.get(model_key, "") if self._config else ""
                url_edit.configure(state="normal")
                key_edit.configure(state="normal")
                url_edit.delete(0, "end")
                key_edit.delete(0, "end")
                if url_val:
                    url_edit.insert(0, url_val)
                if key_val:
                    key_edit.insert(0, key_val)
                url_edit.configure(state="disabled")
                key_edit.configure(state="disabled")
                model_edit.delete(0, "end")
                if model_val:
                    model_edit.insert(0, model_val)
            else:
                # 独立或 ASR：三个字段都从对应配置读取，均可编辑
                # Independent or ASR: all three fields from own config, all editable
                url_val = self._config.get(url_key, "") if self._config else ""
                key_val = self._config.get(apikey_key, "") if self._config else ""
                model_val = self._config.get(model_key, "") if self._config else ""
                url_edit.configure(state="normal")
                key_edit.configure(state="normal")
                url_edit.delete(0, "end")
                key_edit.delete(0, "end")
                if url_val:
                    url_edit.insert(0, url_val)
                if key_val:
                    key_edit.insert(0, key_val)
                model_edit.delete(0, "end")
                if model_val:
                    model_edit.insert(0, model_val)

        # 共用开关切换回调：刷新字段状态（不保存，保存时才统一写入）
        # Share switch toggle callback: refresh field state (no save, save on save button)
        def _on_share_toggled():
            _refresh_fields()

        if is_llm:
            share_checkbox.configure(command=_on_share_toggled)

        # 初次打开时回填字段
        # Fill fields on first open
        _refresh_fields()

        # 保存按钮回调：把字段写入配置并落盘，再关闭弹窗并刷新摘要
        # LLM 共用时：只保存模型名，地址和密钥清空（llm_handler.py 自动回退到 ASR）
        # LLM 独立或 ASR 时：三个字段都保存
        # Save button callback: write fields to config and persist, then close dialog and refresh summary
        # LLM sharing: only save model, clear URL and key (llm_handler.py falls back to ASR)
        # LLM independent or ASR: save all three fields
        def _on_save():
            if not self._config:
                return
            # 先保存共用开关状态（仅 LLM）
            # Save share switch state first (LLM only)
            if is_llm:
                self._config["llm_share_asr"] = bool(share_var.get())
            if is_llm and share_var.get():
                # 共用时：只保存模型名，地址和密钥清空（llm_handler.py 会自动回退用 ASR 的）
                # Sharing: only save model, clear URL and key (llm_handler.py falls back to ASR)
                self._config[model_key] = model_edit.get().strip()
                self._config[url_key] = ""
                self._config[apikey_key] = ""
            else:
                # 独立或 ASR：三个字段都保存
                # Independent or ASR: save all three fields
                self._config[url_key] = url_edit.get().strip()
                self._config[apikey_key] = key_edit.get().strip()
                self._config[model_key] = model_edit.get().strip()
            # 异步保存配置到文件（业务逻辑在 AppController，避免阻塞界面）
            # Async save config to file (business logic in AppController, avoids UI blocking)
            AppController.save_config_to_file(self._config)
            # 关闭弹窗
            # Close dialog
            dialog.destroy()
            # 刷新 AI 页面的配置摘要显示
            # Refresh config summary display on AI page
            self._update_ai_summary()

        # 取消按钮回调：直接关闭弹窗，不保存任何修改
        # Cancel button callback: close dialog without saving any changes
        def _on_cancel():
            dialog.destroy()

        # 重置按钮回调：清空当前弹窗的三个字段（不写入配置，仅清空界面输入框）
        # Reset button callback: clear three fields in dialog (no config write, only clear inputs)
        def _on_reset():
            url_edit.configure(state="normal")
            key_edit.configure(state="normal")
            url_edit.delete(0, "end")
            key_edit.delete(0, "end")
            model_edit.delete(0, "end")
            # 如果是 LLM 且开启共用，重置后仍保持地址密钥灰色不可改（清空后无 ASR 值可显示）
            # If LLM and sharing, keep URL/key disabled after reset (no ASR value to show)
            if is_llm and share_var.get():
                url_edit.configure(state="disabled")
                key_edit.configure(state="disabled")

        # ========== 保存/重置/取消按钮 ==========
        btn_frame = ctk.CTkFrame(dialog, corner_radius=0, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        save_btn = ctk.CTkButton(
            btn_frame, text=_("button.save"), font=(get_font_family(), get_font_size(15), "bold"),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=_on_save, corner_radius=6, height=36
        )
        save_btn.pack(side="left")

        reset_btn = ctk.CTkButton(
            btn_frame, text=_("button.reset"), font=(get_font_family(), get_font_size(15), "bold"),
            fg_color=self.colors.hover, text_color=self.colors.text,
            hover_color=self.colors.active,
            command=_on_reset, corner_radius=6, height=36
        )
        reset_btn.pack(side="left", padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame, text=_("button.cancel"), font=(get_font_family(), get_font_size(15), "bold"),
            fg_color=self.colors.hover, text_color=self.colors.text,
            hover_color=self.colors.active,
            command=_on_cancel, corner_radius=6, height=36
        )
        cancel_btn.pack(side="left", padx=(10, 0))

    def _update_ai_summary(self):
        # 更新 AI 页面两个配置摘要的显示文字
        # ASR 摘要：已配置则显示模型名（或地址），未配置则留空
        # LLM 摘要：开启共用则显示"与ASR共用"，独立则显示 LLM 模型名
        # Update text of two config summaries on AI page
        # ASR summary: if configured show model name (or URL), else empty
        # LLM summary: if share enabled show "share with ASR", else show LLM model name

        # ASR 摘要：从配置读取模型名和地址
        # ASR summary: read model name and URL from config
        if hasattr(self, '_asr_summary_label'):
            asr_model = self._config.get("model", "") if self._config else ""
            asr_url = self._config.get("base_url", "") if self._config else ""
            if asr_model or asr_url:
                # 已配置：优先显示模型名，没有则显示地址
                # Configured: prefer model name, fallback to URL
                self._asr_summary_label.configure(
                    text=_("ai.configured") + ": " + (asr_model if asr_model else asr_url)
                )
            else:
                # 未配置：留空
                # Not configured: empty
                self._asr_summary_label.configure(text="")

        # LLM 摘要：根据共用开关决定显示内容
        # LLM summary: display content based on share switch
        if hasattr(self, '_llm_summary_label'):
            llm_share = self._config.get("llm_share_asr", True) if self._config else True
            if llm_share:
                # 共用 ASR 配置：显示共用提示
                # Sharing ASR config: show share hint
                self._llm_summary_label.configure(text=_("ai.llm_share_asr"))
            else:
                # 独立配置：显示 LLM 模型名
                # Independent config: show LLM model name
                llm_model = self._config.get("llm_model", "") if self._config else ""
                if llm_model:
                    self._llm_summary_label.configure(
                        text=_("ai.configured") + ": " + llm_model
                    )
                else:
                    self._llm_summary_label.configure(text="")

    def _on_diary_changed(self):
        # 日记归档开关切换事件
        enabled = self._diary_switch.get()
        self._save_toolbox_config("diary_enabled", enabled)

    def _on_edit_hotword_file(self):
        # 编辑热词文件按钮点击事件（GUI 部分）
        # 路径计算和文件创建逻辑已抽至 AppController.ensure_config_file()
        import os
        # 调用应用控制器：确保文件存在并返回路径
        hotword_path = AppController.ensure_config_file(
            "hot.txt",
            "# 热词文件，每行一个\n# 格式：热词 = 替换词\n"
        )
        # 用系统默认程序打开
        os.startfile(hotword_path)

    def _on_edit_rule_file(self):
        # 编辑规则文件按钮点击事件（GUI 部分）
        # 路径计算和文件创建逻辑已抽至 AppController.ensure_config_file()
        import os
        # 调用应用控制器：确保文件存在并返回路径
        rule_path = AppController.ensure_config_file(
            "hot-rule.txt",
            "# 正则规则文件，每行一个\n# 格式：模式 = 替换\n"
        )
        # 用系统默认程序打开
        os.startfile(rule_path)

    def _refresh_ui_texts(self):
        # 刷新部分界面文字（语言切换后调用）
        self._logo_label.configure(text=_("app.title"))
        nav_keys = ["nav.home", "nav.log", "nav.history", "nav.ai", "nav.toolbox", "nav.settings"]
        for i, btn in enumerate(self._nav_buttons):
            btn.configure(text=_(nav_keys[i]))
        # 更新开机自启动开关文字
        if hasattr(self, '_autostart_switch'):
            autostart = self._config.get("autostart", False) if self._config else False
            self._autostart_switch.configure(text=_("button.enabled") if autostart else _("button.disabled"))
        # 更新悬浮窗开关文字
        if hasattr(self, '_floating_switch'):
            self._floating_switch.configure(text=_("button.enabled") if self._floating_enabled else _("button.disabled"))

    def _switch_tab(self, index):
        # 切换页面（含懒加载触发）
        # Switch page (with lazy loading trigger)
        self._current_page = index
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color=self.colors.active, text_color=self.colors.text)
            else:
                btn.configure(fg_color="transparent", text_color=self.colors.text_secondary)

        # 懒加载：如果目标页面未创建，先创建
        # Lazy loading: create page if not yet created
        if self._pages[index] is None:
            self._ensure_page_created(index)

        for i, page in enumerate(self._pages):
            if i == index:
                page.pack(fill="both", expand=True)
            elif page is not None:
                page.pack_forget()

        # 切换到历史页面时刷新历史记录列表
        if index == 2:
            self._refresh_history_list()
        # 切换到日志页面时，触发缓冲日志刷新（优化 3：日志页不可见时不刷新）
        # Switch to log page triggers buffered log flush (optimization 3)
        if index == 1 and hasattr(self, '_log_handler') and self._log_handler._buffer:
            # 有缓冲日志时立即触发刷新
            # Trigger immediate flush when there are buffered logs
            if self._log_handler._flush_timer:
                self._root.after_cancel(self._log_handler._flush_timer)
                self._log_handler._flush_timer = None
            self._log_handler._flush()
        # 切换到日志页面时，从文件读取最近的日志显示（优化 C2：磁盘读取方案）
        # 首次切换到日志页时，控件是空的，从 app.log 读取最后 500 行填充
        # Switch to log page loads recent logs from file (optimization C2: disk read)
        # First switch to log page: control is empty, load last 500 lines from app.log
        if index == 1 and hasattr(self, '_log_edit') and self._log_edit.get("1.0", "end-1c").strip() == "":
            self._load_recent_logs_from_file()

    def _apply_theme(self):
        # 应用主题
        # 使用 CustomTkinter �?set_appearance_mode
        if self._theme == THEME_DARK:
            ctk.set_appearance_mode("dark")
            self.colors.apply_dark()
        else:
            ctk.set_appearance_mode("light")
            self.colors.apply_light()

        c = self.colors
        # 更新侧边栏颜�?
        self._sidebar.configure(fg_color=c.sidebar)
        # 更新内容区颜�?
        self._content.configure(fg_color=c.content)
        # 更新页面容器颜色
        self._page_container.configure(fg_color=c.content)
        # 更新Logo标签颜色
        self._logo_label.configure(text_color=c.logo_color)

        # 更新导航按钮颜色
        for i, btn in enumerate(self._nav_buttons):
            if i == self._current_page:
                btn.configure(fg_color=c.active, text_color=c.text)
            else:
                btn.configure(fg_color="transparent", text_color=c.text_secondary)

        # 更新页面背景色和滚动条颜色（CTkScrollableFrame 支持上下滚动）
        # 懒加载：跳过未创建的页面（None）
        # Lazy loading: skip uncreated pages (None)
        for page in self._pages:
            if page is not None:
                page.configure(
                    fg_color=c.content,
                    scrollbar_fg_color="transparent",
                    scrollbar_button_color=c.hover,
                    scrollbar_button_hover_color=c.active
                )

        # 更新主页元素
        if hasattr(self, '_home_title_frame'):
            self._home_title_frame.configure(fg_color=c.content)
        if hasattr(self, '_status_label'):
            self._status_label.configure(text_color=c.text)
        if hasattr(self, '_text_edit'):
            self._text_edit.configure(fg_color=c.card, text_color=c.text)

        # 更新日志页元素
        if hasattr(self, '_log_top_frame'):
            self._log_top_frame.configure(fg_color=c.content)
        if hasattr(self, '_log_edit'):
            self._log_edit.configure(fg_color=c.card, text_color=c.text)
            # 刷新 info tag 的 foreground（创建时设为旧主题的 text 色，切换后需更新）
            # error/warning 用固定红橙色（暗亮通用），info 用 text 色需随主题刷新
            # Refresh info tag foreground (set to old theme's text color on creation, needs update on switch)
            # error/warning use fixed red/orange (common for dark/light), info uses text color, needs refresh
            try:
                self._log_edit.tag_config("info", foreground=c.text)
            except Exception:
                pass

        # 更新AI设置页元�?
        # ASR 输入框已移至统一配置弹窗，主题切换时无需更新页面输入框颜色
        # ASR inputs moved to unified config dialog, no page input color update on theme switch

        # 更新标题标签颜色
        for label in self._title_labels:
            label.configure(text_color=c.text)

        # 更新历史记录页元�?
        if hasattr(self, '_history_top'):
            self._history_top.configure(fg_color=c.content)
        if hasattr(self, '_history_container'):
            self._history_container.configure(
                fg_color=c.content,
                scrollbar_fg_color=c.content,
                scrollbar_button_color=c.card,
                scrollbar_button_hover_color=c.hover
            )

        # 更新下拉框颜色（ttk.Combobox 通过 ttk.Style 配置颜色，不能用 configure）
        # Update combobox colors via ttk.Style (ttk.Combobox doesn't support configure)
        if hasattr(self, '_combo_style'):
            # 重新配置主样式（fieldbackground=输入框背景，selectbackground=下拉列表选中项背景）
            # Reconfigure main style (fieldbackground=input bg, selectbackground=dropdown selected item bg)
            self._combo_style.configure("AICombo.TCombobox",
                fieldbackground=c.card,
                background=c.card,
                foreground=c.text,
                bordercolor=c.border,
                arrowcolor=c.text,
                selectbackground=c.active,
                selectforeground=c.text
            )
            # 同步刷新 map 配置（clam 主题下下拉弹出列表颜色由 map 控制）
            # Sync refresh map config (dropdown popup colors controlled by map in clam theme)
            self._combo_style.map(
                "AICombo.TCombobox",
                selectbackground=[("readonly", c.active)],
                selectforeground=[("readonly", c.text)],
                fieldbackground=[("readonly", c.card)],
                foreground=[("readonly", c.text)]
            )

        # 更新字体大小显示框颜色（CTkLabel，需刷新 fg_color 避免主题切换后白底黑字）
        # Update font size display colors (CTkLabel, refresh fg_color to avoid white bg on theme switch)
        if hasattr(self, '_font_scale_label'):
            self._font_scale_label.configure(fg_color=c.card, text_color=c.text)
        # 更新字体大小上下箭头按钮颜色（次级按钮统一 hover 底）
        # Update font size up/down arrow buttons colors (secondary buttons use hover bg)
        if hasattr(self, '_font_up_btn'):
            self._font_up_btn.configure(fg_color=c.hover, text_color=c.text, hover_color=c.active)
        if hasattr(self, '_font_down_btn'):
            self._font_down_btn.configure(fg_color=c.hover, text_color=c.text, hover_color=c.active)
        # 更新快捷键显示框颜色（已从 CTkEntry 改为 CTkLabel，需刷新 fg_color）
        # Update hotkey display colors (changed from CTkEntry to CTkLabel, need fg_color refresh)
        if hasattr(self, '_hotkey_entry'):
            self._hotkey_entry.configure(fg_color=c.card, text_color=c.text)

        # 更新开机自启动复选框颜色
        if hasattr(self, '_autostart_switch'):
            self._autostart_switch.configure(
                fg_color=c.accent, border_color=c.text_secondary,
                checkmark_color="white", hover_color=c.hover,
                text_color=c.text
            )

        # 更新悬浮窗复选框颜色
        if hasattr(self, '_floating_switch'):
            self._floating_switch.configure(
                fg_color=c.accent, border_color=c.text_secondary,
                checkmark_color="white", hover_color=c.hover,
                text_color=c.text
            )

        # 更新工具箱页面元素颜色
        if hasattr(self, '_threshold_slider'):
            self._threshold_slider.configure(
                fg_color=c.card, progress_color=c.accent,
                button_color=c.accent, button_hover_color=c.hover
            )
        if hasattr(self, '_threshold_label'):
            self._threshold_label.configure(text_color=c.text_secondary)
        # 更新工具箱页各开关颜色（CheckBox 的 border_color/text_color 随主题变化）
        # Update toolbox switches colors (CheckBox border_color/text_color follow theme)
        for _sw in ('_punct_switch', '_itn_switch', '_hot_switch',
                    '_rule_switch', '_filler_switch', '_diary_switch'):
            _w = getattr(self, _sw, None)
            if _w is not None:
                _w.configure(
                    fg_color=c.accent, border_color=c.text_secondary,
                    hover_color=c.hover, text_color=c.text
                )
        # 更新工具箱页编辑文件按钮颜色（fg_color=hover 随主题变化，不刷新会颜色错位）
        # Update toolbox edit-file buttons colors (fg_color=hover follows theme)
        if hasattr(self, '_edit_hot_btn'):
            self._edit_hot_btn.configure(fg_color=c.hover, text_color=c.text, hover_color=c.active)
        if hasattr(self, '_edit_rule_btn'):
            self._edit_rule_btn.configure(fg_color=c.hover, text_color=c.text, hover_color=c.active)
        # 更新 AI 页配置按钮颜色（accent 蓝色通用，但 hover_color 需刷新）
        # Update AI page config buttons colors (accent blue is common, but hover_color needs refresh)
        if hasattr(self, '_asr_config_btn'):
            self._asr_config_btn.configure(fg_color=c.accent, hover_color=c.hover)
        if hasattr(self, '_llm_config_btn'):
            self._llm_config_btn.configure(fg_color=c.accent, hover_color=c.hover)
        # 更新 AI 页摘要标签颜色（text_color 随主题变化）
        # Update AI page summary labels colors (text_color follows theme)
        if hasattr(self, '_asr_summary_label'):
            self._asr_summary_label.configure(text_color=c.text_secondary)
        if hasattr(self, '_llm_summary_label'):
            self._llm_summary_label.configure(text_color=c.text_secondary)
        # 更新 AI 页去除语气词开关颜色（已移至工具箱页）
        # Update filler switch colors (moved to toolbox page)
        if hasattr(self, '_filler_switch'):
            self._filler_switch.configure(
                fg_color=c.accent, border_color=c.text_secondary,
                hover_color=c.hover
            )
        # 更新 AI 页 LLM 文本润色总开关颜色
        # Update AI page LLM text polish master switch colors
        if hasattr(self, '_ai_llm_switch'):
            self._ai_llm_switch.configure(
                fg_color=c.accent, border_color=c.border,
                hover_color=c.hover, text_color=c.text
            )
        # 更新 AI 页 LLM 角色开关颜色
        # Update AI page LLM role switch colors
        if hasattr(self, '_ai_llm_role_switch'):
            self._ai_llm_role_switch.configure(
                fg_color=c.accent, border_color=c.border,
                hover_color=c.hover, text_color=c.text
            )
        # LLM 输入框已移至统一配置弹窗，主题切换时无需更新页面输入框颜色
        # LLM inputs moved to unified config dialog, no page input color update on theme switch

        # 刷新历史记录列表样式
        self._refresh_history_list()

        # 更新悬浮窗颜色（主题切换时同步背景和文字颜色）
        # Update floating window colors on theme switch (sync bg and text colors)
        if self.floating_window is not None:
            self.floating_window.apply_theme(self.colors)

    def _set_theme(self, theme):
        self._theme = theme
        self._apply_theme()
        self._update_theme_combo()
        self._save_theme_to_config()

    def _save_theme_to_config(self):
        # 保存主题到配置（业务逻辑已移至 app_controller.py）
        if self._config is None:
            return
        theme_str = "light" if self._theme == THEME_LIGHT else "dark"
        AppController.save_theme_to_config(self._config, theme_str)

    def _update_theme_combo(self):
        # 更新主题下拉框状�?
        if hasattr(self, '_theme_combo'):
            theme_display = _("settings.theme_light") if self._theme == THEME_LIGHT else _("settings.theme_dark")
            self._theme_var.set(theme_display)

    def _update_autostart_switch(self):
        # 更新自启动开关状态（从配置加载后同步界面）
        if not self._config:
            return
        autostart = self._config.get("autostart", False)
        if hasattr(self, '_autostart_switch'):
            if autostart:
                self._autostart_switch.select()
            else:
                self._autostart_switch.deselect()
            # 更新开关旁的文字
            self._autostart_switch.configure(text=_("button.enabled") if autostart else _("button.disabled"))

    def _save_floating_to_config(self):
        # 保存悬浮窗设置到配置（业务逻辑已移至 app_controller.py）
        if self._config is None:
            return
        AppController.save_floating_to_config(self._config, self._floating_enabled)

    def update_floating_status(self, status):
        if self.floating_window and self._floating_enabled:
            self.floating_window.set_status(status)

    def update_floating_result(self, result):
        pass

    def copy_to_clipboard(self, text):
        if not text:
            return
        self._root.clipboard_clear()
        self._root.clipboard_append(text)

    def _copy_to_clipboard(self, text):
        if not text:
            self._status_label.configure(text=_("status.nothing_to_copy"))
            return
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._status_label.configure(text=_("status.copied"))

    def _copy_and_save(self):
        text = self._text_edit.get("1.0", "end-1c").strip()
        if not text:
            self._status_label.configure(text=_("status.nothing_to_copy"))
            return
        self._copy_to_clipboard(text)
        # 延迟加载保护：历史记录可能尚未加载
        # Lazy load protection: history may not be loaded yet
        if self._history is None:
            self._history = AppController.load_history()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._history.append({"time": timestamp, "text": text})
        self._text_edit.delete("1.0", "end")
        self._recognized_text = ""
        self._status_label.configure(text=_("status.copied_and_saved"))

    def append_to_history(self, text):
        # 追加识别结果到历史记录（GUI 部分）
        # 保存逻辑已抽至 AppController.save_history_async()，异步执行避免阻塞主线程
        if not text:
            return
        # 延迟加载：如果历史记录尚未加载，先加载
        # Lazy load: load history if not yet loaded
        if self._history is None:
            self._history = AppController.load_history()
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 添加到内存中的历史记录列表
        self._history.append({"time": timestamp, "text": text})
        # 限制历史记录最大数量，防止内存和磁盘占用无限增长
        # 超过 1000 条时删除最旧的记录
        # Limit max history count to prevent unbounded memory/disk usage
        # Delete oldest records when exceeding 1000
        MAX_HISTORY = 1000
        if len(self._history) > MAX_HISTORY:
            # 保留最新的 1000 条（删除前面多余的）
            # Keep newest 1000 records (delete excess from front)
            del self._history[:len(self._history) - MAX_HISTORY]
        # 异步保存到文件（避免每次识别结果都阻塞主线程导致界面卡顿）
        # Async save to file (avoid blocking main thread on every recognition result)
        AppController.save_history_async(self._history)
        logger.info("GUI: 识别结果已自动保存到历史记录: %s", text[:50])

    def _refresh_history_list(self):
        # 刷新历史记录列表显示
        # 懒加载：history 页面可能未创建，此时跳过
        # Lazy loading: history page may not be created yet, skip in that case
        if not hasattr(self, '_history_container'):
            return
        # 延迟加载：首次访问时才从文件读取历史记录
        # Lazy load: read history from file on first access
        if self._history is None:
            self._history = AppController.load_history()
        for widget in self._history_container.winfo_children():
            widget.destroy()
        for item in reversed(self._history):
            self._add_history_card(item)

    def _add_history_card(self, item):
        # 创建卡片框架，使�?CustomTkinter
        card = ctk.CTkFrame(self._history_container, corner_radius=6)
        card.pack(fill="x", pady=(0, 0))

        # 创建间隔框架，使用内容背景色（使�?CustomTkinter 确保主题一致性）
        spacer = ctk.CTkFrame(self._history_container, corner_radius=0, height=15, fg_color=self.colors.content)
        spacer.pack(fill="x")

        # 创建卡片顶部框架
        top = ctk.CTkFrame(card, corner_radius=0)
        top.pack(fill="x", padx=15, pady=(10, 5))

        # 创建时间标签
        ctk.CTkLabel(
            top, text=item['time'], font=(get_font_family(), get_font_size(14)),
            text_color=self.colors.text_secondary
        ).pack(side="left")

        # 创建复制按钮
        copy_btn = ctk.CTkButton(
            top, text=_("button.copy"), font=(get_font_family(), get_font_size(14)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=lambda t=item['text']: self._copy_to_clipboard(t),
            corner_radius=6,
            height=26
        )
        copy_btn.pack(side="right", padx=(5, 0))

        # 创建删除按钮（使�?config.json 中的 danger 颜色�?
        delete_btn = ctk.CTkButton(
            top, text=_("button.delete"), font=(get_font_family(), get_font_size(14)),
            fg_color=self.colors.danger, text_color="white",
            hover_color=self.colors.danger_hover,
            command=lambda t=item: self._delete_history_item(t),
            corner_radius=6,
            height=26
        )
        delete_btn.pack(side="right")

        # 创建文本预览标签（左对齐 + 段首空两格）
        # 使用两个全角空格实现中文排版习惯的段首缩�?
        text_preview = item['text'][:100] + "..." if len(item['text']) > 100 else item['text']
        text_preview = "\u3000\u3000" + text_preview  # 段首添加两个全角空格（缩进两字符�?
        ctk.CTkLabel(
            card, text=text_preview, font=(get_font_family(), get_font_size(15)),
            text_color=self.colors.text,
            wraplength=600, justify="left", anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 10))

    def _delete_history_item(self, item):
        # 延迟加载保护：历史记录可能尚未加载
        # Lazy load protection: history may not be loaded yet
        if self._history is None:
            return
        if item in self._history:
            self._history.remove(item)
            self._refresh_history_list()
            self._status_label.configure(text=_("status.deleted"))

    def _clear_history(self):
        # 清空历史记录（GUI 部分）
        # 清空文件的业务逻辑已抽至 AppController.clear_history()
        self._history = []  # 设为空列表（不是 None），表示已加载但无记录
        # 刷新历史记录列表显示
        self._refresh_history_list()
        # 调用应用控制器：清空历史记录文件
        AppController.clear_history()
        self._status_label.configure(text=_("status.history_cleared"))

    def _copy_log(self):
        text = self._log_edit.get("1.0", "end-1c").strip()
        if not text:
            self._status_label.configure(text=_("status.log_empty"))
            return
        self._copy_to_clipboard(text)

    def _clear_log(self):
        # 清空日志页面显示的内容
        # Clear the log display content
        self._log_edit.configure(state="normal")
        self._log_edit.delete("1.0", "end")
        self._log_edit.configure(state="disabled")
        self._status_label.configure(text=_("status.log_cleared"))

    def _export_log(self):
        # 导出日志为TXT文件，默认保存到桌面
        # Export log to TXT file, default save to desktop
        # 获取日志文本
        # Get log text
        text = self._log_edit.get("1.0", "end-1c").strip()
        if not text:
            self._status_label.configure(text=_("status.log_empty"))
            return
        # 弹出文件保存对话框
        # Show file save dialog
        from tkinter import filedialog
        # 生成默认文件名（带时间戳）
        # Generate default filename (with timestamp)
        import datetime
        import os
        default_name = f"语音输入日志_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        # 获取桌面路径作为默认保存目录
        # Get desktop path as default save directory
        desktop_path = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        file_path = filedialog.asksaveasfilename(
            title=_("button.export"),
            defaultextension=".txt",
            filetypes=[("TXT", "*.txt"), ("All Files", "*.*")],
            initialfile=default_name,
            initialdir=desktop_path,
        )
        # 如果用户取消了保存
        # If user cancelled save
        if not file_path:
            return
        # 写入文件
        # Write to file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self._status_label.configure(text=_("status.log_exported"))
        except Exception as e:
            self._status_label.configure(text=_("status.log_export_error") + f": {e}")

    def load_settings(self, config: dict):
        # 加载配置到 AI 设置页面（开关状态 + 刷新摘要）
        # ASR/LLM 的 API 配置不在页面输入框显示，由弹窗读取 config
        # 共用开关和 API 配置已移入弹窗，这里只加载去除语气词开关
        # Load config to AI settings page (switch states + refresh summary)
        # ASR/LLM API configs not shown in page inputs, read by dialog from config
        # Share switch and API configs moved into dialog, here only load remove filler switch
        if not config:
            return
        # 懒加载触发：确保 AI 页面已创建（开关控件需要先存在）
        # Lazy load trigger: ensure AI page is created (switch widgets must exist first)
        self._ensure_page_created(3)
        self._config = config
        # 加载去除语气词开关状态（默认关闭，已移至工具箱页）
        # Load remove filler words switch state (default False, moved to toolbox page)
        if hasattr(self, '_filler_switch'):
            filler_val = config.get("llm_remove_filler", False)
            if filler_val:
                self._filler_switch.select()
            else:
                self._filler_switch.deselect()
        # 加载 LLM 润色和角色开关状态
        # Load LLM polish and role switch states
        llm_on = config.get("llm_enabled", False)
        if hasattr(self, '_ai_llm_switch_var'):
            self._ai_llm_switch_var.set(llm_on)
        if hasattr(self, '_ai_llm_role_var'):
            self._ai_llm_role_var.set(llm_on)
            self._ai_llm_role_switch.configure(state="normal" if llm_on else "disabled")
        # 刷新 AI 页面配置摘要显示
        # Refresh AI page config summary display
        self._update_ai_summary()

    def start(self):
        # 启动GUI（设置日志处理器等）
        # 创建自定义日志处理器，将日志输出到GUI日志页面
        # Create custom log handler to output logs to GUI log page

        # 懒加载触发：确保日志页面已创建（GuiLogHandler 需要 _log_edit 控件）
        # Lazy load trigger: ensure log page is created (GuiLogHandler needs _log_edit widget)
        self._ensure_page_created(1)

        class GuiLogHandler(logging.Handler):
            # 自定义日志处理器
            # 使用批量更新机制：日志先入缓冲区，100ms后批量刷新到界面
            # 减少频繁的界面重绘，提升流畅度
            # Custom log handler
            # Uses batch update: logs enter buffer first, flush to GUI after 100ms
            # Reduces frequent GUI redraws, improves smoothness

            def __init__(self, gui_instance):
                # 初始化处理器
                # Initialize handler
                super().__init__()
                # 保存GUI实例引用
                # Save GUI instance reference
                self.gui = gui_instance
                # 设置日志级别为INFO
                # Set log level to INFO
                self.setLevel(logging.INFO)
                # 日志缓冲区，积攒日志用于批量更新
                # Log buffer, accumulate logs for batch update
                self._buffer = []
                # 定时器ID，用于避免重复启动定时器
                # Timer ID, used to avoid duplicate timer starts
                self._flush_timer = None

            def emit(self, record):
                # 处理日志记录：加入缓冲区，启动定时器批量刷新
                # 同时保存日志级别（levelno），用于 GUI 按级别着色
                # Process log record: add to buffer, start timer for batch flush
                # Also save log level (levelno) for GUI coloring by level
                try:
                    # 格式化日志消息
                    # Format log message
                    msg = self.format(record)
                    # 加入缓冲区（消息 + 级别），不立即更新界面
                    # Add to buffer (message + level), don't update GUI immediately
                    self._buffer.append((msg, record.levelno))
                    # 如果定时器未启动且窗口存在，启动100ms定时器
                    # If timer not started and window exists, start 100ms timer
                    if self._flush_timer is None and self.gui._root.winfo_exists():
                        self._flush_timer = self.gui._root.after(100, self._flush)
                except Exception as e:
                    # 记录GUI日志处理异常的调试日志
                    # Record debug log for GUI log handler exception
                    logger.debug("GUI: 日志处理异常: %s", e)
                    # 调用logging标准错误处理
                    # Call logging standard error handling
                    self.handleError(record)

            def _flush(self):
                # 批量刷新缓冲区到界面（100ms内积攒的日志一次性显示）
                # Batch flush buffer to GUI (logs accumulated within 100ms displayed at once)
                # _flush 在主线程通过 after() 调用，emit 在日志线程被 logging 模块加锁调用
                # 此处用 self.lock（继承自 logging.Handler）保护 _buffer 跨线程读写
                # _flush called in main thread via after(), emit called in logger thread with lock held by logging
                # Use self.lock (inherited from logging.Handler) to protect _buffer cross-thread access
                # 清空定时器ID
                # Clear timer ID
                self._flush_timer = None
                # 加锁访问缓冲区，防止与 emit 中的 append 竞态
                # Lock buffer access, prevent race with append in emit
                with self.lock:
                    # 如果缓冲区为空，直接返回
                    # If buffer is empty, return directly
                    if not self._buffer:
                        return
                    # 性能优化：日志页面不可见时不刷新界面，只保留缓冲区
                    # 切换到日志页面时会触发一次刷新
                    # Performance: skip GUI refresh when log page not visible, keep buffer
                    # Switching to log page triggers a flush
                    if self.gui._current_page != 1:
                        # 缓冲区上限保护：超过 500 条时丢弃最旧的，防止内存无限增长
                        # Buffer cap: discard oldest when exceeding 500, prevent unbounded memory
                        if len(self._buffer) > 500:
                            del self._buffer[:len(self._buffer) - 500]
                        return
                    # 取出所有缓冲的日志（每条包含消息和级别）
                    # Get all buffered logs (each contains message and level)
                    logs = self._buffer[:]
                    self._buffer.clear()
                # 批量插入到日志框（在主线程中执行，传递级别用于着色）
                # 锁外执行 GUI 操作，避免长时间持锁
                # Batch insert to log box (execute in main thread, pass level for coloring)
                # GUI operations outside lock to avoid holding lock too long
                if self.gui._root.winfo_exists():
                    for msg, level in logs:
                        self.gui.append_log(msg, level)
        
        # 创建并添加GUI日志处理器
        # Create and add GUI log handler
        gui_handler = GuiLogHandler(self)
        # 设置日志格式：时间 - 级别 - 消息
        # Set log format: time - level - message
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        gui_handler.setFormatter(formatter)
        # 将处理器添加到VoiceInput日志记录器
        # Add handler to VoiceInput logger
        logging.getLogger("VoiceInput").addHandler(gui_handler)
        # 保存引用，供 _switch_tab 切换到日志页时触发刷新
        # Save reference for _switch_tab to trigger flush when switching to log page
        self._log_handler = gui_handler

    def mainloop(self):
        # 启动tkinter主事件循�?
        self._root.mainloop()

    def bring_to_front(self):
        # 将主窗口前置
        self._root.deiconify()
        self._root.lift()
        self._root.attributes("-topmost", True)
        self._root.after(100, lambda: self._root.attributes("-topmost", False))

    def stop(self):
        # 停止主窗口（兼容接口�?
        pass

    def run(self):
        # 启动主循环（兼容旧接口）
        self._root.mainloop()

    def close(self):
        # 关闭主窗口（隐藏窗口但不退出程序，托盘图标保持�?
        if self.floating_window:
            self.floating_window.hide()
        self.hide()

    def hide(self):
        # 隐藏主窗�?
        self._root.withdraw()

    def show(self):
        # 显示主窗�?
        self._root.deiconify()

    def append_log(self, message, level=logging.INFO):
        # 添加日志到 GUI 日志框，按级别着色
        # level: 日志级别数字（logging.INFO=20, WARNING=30, ERROR=40, CRITICAL=50）
        # 注：日志同时写入文件（TimedRotatingFileHandler），这里只负责 GUI 显示
        # Add log to GUI log box, colored by level
        # level: log level number (logging.INFO=20, WARNING=30, ERROR=40, CRITICAL=50)
        # Note: log also written to file (TimedRotatingFileHandler), here only for GUI display
        if hasattr(self, '_log_edit'):
            self._log_edit.configure(state="normal")
            # 根据日志级别选择对应的 tag（颜色）
            # Select tag (color) based on log level
            if level >= logging.ERROR:
                # ERROR/CRITICAL：红色加粗
                # ERROR/CRITICAL: red bold
                tag = "error"
            elif level >= logging.WARNING:
                # WARNING：橙色
                # WARNING: orange
                tag = "warning"
            else:
                # INFO/DEBUG：默认颜色
                # INFO/DEBUG: default color
                tag = "info"
            # 插入文本时应用对应的 tag
            # Insert text with corresponding tag
            self._log_edit.insert("end", message + "\n", tag)
            # 限制日志框行数，超过 500 行时删除最旧的
            # 防止长时间运行后内存无限增长
            # Limit log box lines, delete oldest when exceeding 500
            # Prevents unbounded memory growth on long runs
            line_count = int(self._log_edit.index("end-1c").split(".")[0])
            if line_count > 500:
                # 删除前面多余的行，保留最后 500 行
                # Delete excess lines from front, keep last 500
                self._log_edit.delete("1.0", f"{line_count - 500}.0")
            self._log_edit.see("end")
            self._log_edit.configure(state="disabled")

    def _load_recent_logs_from_file(self):
        # 从日志文件读取最后 500 行显示到日志框（优化 C2：磁盘读取方案）
        # 首次切换到日志页时调用，让用户能看到本次启动前的历史日志
        # 同时解析每行的日志级别，按级别着色（ERROR 红色加粗、WARNING 橙色、INFO 默认）
        # Load last 500 lines from log file to log box (optimization C2: disk read)
        # Called on first switch to log page, shows history logs before this startup
        # Also parses log level per line, colors by level (ERROR red bold, WARNING orange, INFO default)
        try:
            from .app_utils import LOG_FILE
            # 读取日志文件最后 500 行
            # Read last 500 lines from log file
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            if recent_lines:
                self._log_edit.configure(state="normal")
                # 逐行解析级别并插入（日志格式：时间 - LEVEL - 消息）
                # Parse level per line and insert (log format: time - LEVEL - message)
                for line in recent_lines:
                    # 通过字符串匹配判断日志级别
                    # Determine log level by string matching
                    if " - ERROR - " in line or " - CRITICAL - " in line:
                        tag = "error"
                    elif " - WARNING - " in line:
                        tag = "warning"
                    else:
                        tag = "info"
                    # 插入该行（保留原始换行符）
                    # Insert line (preserve original newline)
                    self._log_edit.insert("end", line if line.endswith("\n") else line + "\n", tag)
                self._log_edit.see("end")
                self._log_edit.configure(state="disabled")
        except Exception as e:
            logger.debug("GUI: 读取日志文件失败: %s", e)

    def set_status(self, status):
        # 更新状态标�?
        if hasattr(self, '_status_label'):
            self._status_label.configure(text=status)

    def set_recognized_text(self, text):
        # 设置识别文本
        self._recognized_text = text
        if hasattr(self, '_text_edit'):
            self._text_edit.delete("1.0", "end")
            self._text_edit.insert("1.0", text)

    def append_text(self, text):
        # 追加文本到识别文�?
        self._recognized_text = self._recognized_text + text if self._recognized_text else text
        if hasattr(self, '_text_edit'):
            self._text_edit.insert("end", text)

    def update_text(self, text):
        # 更新识别文本（替换）
        self._recognized_text = text
        if hasattr(self, '_text_edit'):
            self._text_edit.delete("1.0", "end")
            self._text_edit.insert("1.0", text)

    def set_config(self, config: dict):
        # 设置配置到主窗口（填充输入框内容�?
        self._config = config
        self.load_settings(config)

    def set_on_close_callback(self, callback):
        # 设置窗口关闭时的回调函数
        self._on_close_callback = callback
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    def set_hotkey_callbacks(self, pause_cb, resume_cb):
        # 设置热键监听器的暂停/恢复回调（用于设置页捕获热键时避免冲突）
        # Set hotkey listener pause/resume callbacks (avoid conflict when capturing in settings)
        self._pause_hotkey = pause_cb
        self._resume_hotkey = resume_cb

    def bind_close(self, callback):
        # 绑定关闭回调（兼容旧接口�?
        self.set_on_close_callback(callback)

    def _on_close(self):
        # 关闭处理
        if self._on_close_callback:
            self._on_close_callback()
        else:
            self.close()

    def _create_log_page(self):
        page = ctk.CTkScrollableFrame(self._page_container, corner_radius=0)

        log_top_frame = ctk.CTkFrame(page, corner_radius=0)
        log_top_frame.pack(fill="x", padx=30, pady=(20, 10))
        self._log_top_frame = log_top_frame

        log_title = ctk.CTkLabel(
            log_top_frame, text=_("log.title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(log_title)
        log_title.pack(side="left")

        copy_log_btn = ctk.CTkButton(
            log_top_frame, text=_("button.copy"), font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=self._copy_log,
            corner_radius=6,
            height=30
        )
        copy_log_btn.pack(side="right")

        # 导出日志按钮（导出为TXT文件）
        # Export log button (export to TXT file)
        export_log_btn = ctk.CTkButton(
            log_top_frame, text=_("button.export"), font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=self._export_log,
            corner_radius=6,
            height=30
        )
        export_log_btn.pack(side="right", padx=(0, 10))

        # 清空日志按钮（样式与历史记录页面的清空按钮一致）
        # Clear log button (style consistent with history page's clear button)
        clear_log_btn = ctk.CTkButton(
            log_top_frame, text=_("button.clear"), font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=self._clear_log,
            corner_radius=6,
            height=30
        )
        clear_log_btn.pack(side="right", padx=(0, 10))

        self._log_edit = ctk.CTkTextbox(
            page, font=(get_font_family(), get_font_size(14)),
            fg_color=self.colors.card, text_color=self.colors.text,
            corner_radius=6,
            height=300,
            state="disabled"
        )
        self._log_edit.pack(fill="x", padx=30, pady=(0, 15))

        # 配置日志级别颜色 tag（CTkTextbox 基于 tkinter.Text，支持 tag_config）
        # 注：CTkTextbox 不允许在 tag_config 中设置 font（与缩放不兼容），只能设置颜色
        # ERROR/CRITICAL：红色，最显眼，方便快速定位错误
        # WARNING：橙色，次要提醒
        # INFO：默认颜色，普通信息
        # Configure log level color tags (CTkTextbox based on tkinter.Text, supports tag_config)
        # Note: CTkTextbox forbids font in tag_config (incompatible with scaling), only color allowed
        # ERROR/CRITICAL: red, most visible, easy to locate errors
        # WARNING: orange, secondary alert
        # INFO: default color, normal info
        self._log_edit.tag_config("error", foreground="#D9534F", background="#FFE5E5")
        self._log_edit.tag_config("warning", foreground="#E68A00")
        self._log_edit.tag_config("info", foreground=self.colors.text)

        return page

    def _create_history_page(self):
        page = ctk.CTkScrollableFrame(self._page_container, corner_radius=0)

        self._history_top = ctk.CTkFrame(page, corner_radius=0)
        self._history_top.pack(fill="x", padx=30, pady=(20, 10))

        self._history_title = ctk.CTkLabel(
            self._history_top, text=_("history.title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(self._history_title)
        self._history_title.pack(side="left")

        clear_btn = ctk.CTkButton(
            self._history_top, text=_("button.clear"), font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=self._clear_history,
            corner_radius=6,
            height=30
        )
        clear_btn.pack(side="right")

        # 历史记录滚动区域使用 CustomTkinter �?CTkScrollableFrame
        self._history_container = ctk.CTkScrollableFrame(
            page, corner_radius=0,
            fg_color=self.colors.content,
            scrollbar_fg_color=self.colors.content,
            scrollbar_button_color=self.colors.card,
            scrollbar_button_hover_color=self.colors.hover
        )
        self._history_container.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        return page

    def _create_ai_page(self):
        page = ctk.CTkScrollableFrame(self._page_container, corner_radius=0)

        ai_title = ctk.CTkLabel(
            page, text=_("ai.title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(ai_title)
        ai_title.pack(anchor="w", padx=30, pady=(20, 20))

        # ========== 语音识别（ASR）配置 ==========
        # 统一弹窗方案：点击按钮弹出配置弹窗，前缀 "" 保存到 base_url/api_key/model
        # Unified dialog approach: click button to open config dialog, prefix "" saves to base_url/api_key/model
        asr_btn = ctk.CTkButton(
            page, text=_("ai.config_asr"), font=(get_font_family(), get_font_size(17), "bold"),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=lambda: self.show_api_config_dialog("ai.config_asr", ""),
            corner_radius=6, height=40
        )
        asr_btn.pack(anchor="w", padx=30, pady=(0, 5))
        self._asr_config_btn = asr_btn

        # ASR 配置摘要（显示已配置的模型名或地址，未配置则留空）
        # ASR config summary (shows configured model name or URL, empty if not configured)
        self._asr_summary_label = ctk.CTkLabel(
            page, text="", font=(get_font_family(), get_font_size(14)),
            text_color=self.colors.text_secondary
        )
        self._asr_summary_label.pack(anchor="w", padx=30, pady=(0, 20))
        # 初始刷新 ASR 摘要显示（从已加载的配置读取）
        # Refresh ASR summary display initially (from loaded config)
        self._update_ai_summary()

        # ========== LLM 文本润色设置 ==========
        # LLM 区块标题
        # LLM section title
        llm_title = ctk.CTkLabel(
            page, text=_("ai.llm_title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(llm_title)
        llm_title.pack(anchor="w", padx=30, pady=(10, 10))

        # "与 ASR 共用配置"开关已移至 LLM 弹窗内（避免页面层级混乱）
        # "Share with ASR" switch moved into LLM dialog (avoid messy page hierarchy)

        # LLM 文本润色总开关：控制是否启用 LLM 处理
        # LLM text polishing master switch: control whether to enable LLM processing
        llm_enabled = self._config.get("llm_enabled", False) if self._config else False
        self._ai_llm_switch_var = tk.BooleanVar(value=llm_enabled)
        self._ai_llm_switch = ctk.CTkCheckBox(
            page, text=_("ai.llm_enabled"), font=(get_font_family(), get_font_size(15)),
            variable=self._ai_llm_switch_var,
            fg_color=self.colors.accent, hover_color=self.colors.hover,
            border_color=self.colors.border,
            checkmark_color="white",
            text_color=self.colors.text,
            corner_radius=6,
            command=self._on_ai_llm_switch_changed
        )
        self._ai_llm_switch.pack(anchor="w", padx=30, pady=(0, 10))

        # LLM 配置按钮：点击弹出统一配置弹窗，前缀 "llm_" 保存到 llm_base_url/llm_api_key/llm_model
        # LLM config button: click to open unified dialog, prefix "llm_" saves to llm_*
        llm_btn = ctk.CTkButton(
            page, text=_("ai.config_llm"), font=(get_font_family(), get_font_size(17), "bold"),
            fg_color=self.colors.accent, text_color="white",
            hover_color=self.colors.hover,
            command=lambda: self.show_api_config_dialog("ai.config_llm", "llm_"),
            corner_radius=6, height=40
        )
        llm_btn.pack(anchor="w", padx=30, pady=(0, 5))
        self._llm_config_btn = llm_btn

        # LLM 配置摘要（共用时显示"与ASR共用"提示，独立时显示模型名）
        # LLM config summary (shows "share with ASR" hint when sharing, model name when independent)
        self._llm_summary_label = ctk.CTkLabel(
            page, text="", font=(get_font_family(), get_font_size(14)),
            text_color=self.colors.text_secondary
        )
        self._llm_summary_label.pack(anchor="w", padx=30, pady=(0, 15))

        # LLM 角色开关（从工具箱页移至此处，仅润色启用时可选）
        # LLM role switch (moved from toolbox page, only selectable when polish enabled)
        llm_role_enabled = self._config.get("llm_enabled", False) if self._config else False
        self._ai_llm_role_var = tk.BooleanVar(value=llm_role_enabled)
        self._ai_llm_role_switch = ctk.CTkCheckBox(
            page, text=_("ai.llm_role"), font=(get_font_family(), get_font_size(15)),
            variable=self._ai_llm_role_var,
            fg_color=self.colors.accent, hover_color=self.colors.hover,
            border_color=self.colors.border,
            checkmark_color="white",
            text_color=self.colors.text,
            corner_radius=6,
            command=self._on_ai_llm_role_changed,
            state="normal" if llm_role_enabled else "disabled"
        )
        self._ai_llm_role_switch.pack(anchor="w", padx=30, pady=(0, 15))

        return page

    def _on_ai_llm_role_changed(self):
        # AI 页 LLM 角色开关切换事件（即时保存）
        # AI page LLM role switch toggle event (instant save)
        if not self._config:
            return
        enabled = self._ai_llm_role_var.get()
        self._config["llm_enabled"] = enabled
        AppController.save_config_to_file(self._config)
        # 同步 AI 页润色总开关
        # Sync AI page polish switch
        if hasattr(self, '_ai_llm_switch_var'):
            self._ai_llm_switch_var.set(enabled)

    def _on_ai_llm_switch_changed(self):
        # AI 设置页 LLM 文本润色总开关切换事件（即时保存）
        # 润色关闭时，LLM 角色开关也关闭并禁用；开启时恢复可选
        # AI settings page LLM text polishing master switch toggle event (instant save)
        # When polish off, role switch also off and disabled; when on, restore selectable
        if not self._config:
            return
        enabled = self._ai_llm_switch_var.get()
        self._config["llm_enabled"] = enabled
        AppController.save_config_to_file(self._config)
        # 同步 AI 页角色开关：润色关闭→角色也关闭且禁用；润色开启→角色可选
        # Sync AI page role switch: polish off→role off and disabled; polish on→role selectable
        if hasattr(self, '_ai_llm_role_var'):
            self._ai_llm_role_var.set(enabled)
            self._ai_llm_role_switch.configure(state="normal" if enabled else "disabled")

    def _on_filler_changed(self):
        # 去除语气词开关切换事件（工具箱页，即时保存）
        # Remove filler words switch toggle event (toolbox page, instant save)
        if not self._config:
            return
        self._config["llm_remove_filler"] = bool(self._filler_switch.get())
        AppController.save_config_to_file(self._config)

    def _create_toolbox_page(self):
        # 创建工具箱页面
        # 包含：去除末尾标点、ITN数字转换、热词替换+阈值、正则替换、
        #       LLM角色+API配置、日记归档、编辑热词/规则文件按钮
        # Create toolbox page
        # Includes: remove trailing punctuation, ITN, hotword+threshold, regex,
        #           LLM role+API config, diary, edit hotword/rule file buttons

        page = ctk.CTkScrollableFrame(self._page_container, corner_radius=0)

        # ========== 页面标题 ==========
        toolbox_title = ctk.CTkLabel(
            page, text=_("toolbox.title"), font=(get_font_family(), get_font_size(17), "bold"),
            text_color=self.colors.text
        )
        self._title_labels.append(toolbox_title)
        toolbox_title.pack(anchor="w", padx=30, pady=(20, 20))

        # ========== 去除末尾标点开关 ==========
        punct_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        punct_frame.pack(fill="x", padx=30, pady=(0, 5))

        punct_label = ctk.CTkLabel(
            punct_frame, text=_("toolbox.remove_punct"), font=(get_font_family(), get_font_size(17)),
            text_color=self.colors.text
        )
        self._title_labels.append(punct_label)
        punct_label.pack(side="left")

        # 从配置读取当前值，默认开启
        punct_enabled = self._config.get("remove_trailing_punct", True) if self._config else True
        self._punct_switch = ctk.CTkCheckBox(
            punct_frame, text="",
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            checkbox_width=24, checkbox_height=24,
            command=self._on_punct_changed
        )
        self._punct_switch.pack(side="right")
        # 设置开关状态
        if punct_enabled:
            self._punct_switch.select()
        else:
            self._punct_switch.deselect()

        # ========== ITN数字转换开关 ==========
        itn_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        itn_frame.pack(fill="x", padx=30, pady=(10, 5))

        itn_label = ctk.CTkLabel(
            itn_frame, text=_("toolbox.itn"), font=(get_font_family(), get_font_size(17)),
            text_color=self.colors.text
        )
        self._title_labels.append(itn_label)
        itn_label.pack(side="left")

        # 从配置读取当前值，默认开启
        itn_enabled = self._config.get("itn_enabled", True) if self._config else True
        self._itn_switch = ctk.CTkCheckBox(
            itn_frame, text="",
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            checkbox_width=24, checkbox_height=24,
            command=self._on_itn_changed
        )
        self._itn_switch.pack(side="right")
        if itn_enabled:
            self._itn_switch.select()
        else:
            self._itn_switch.deselect()

        # ========== 热词替换开关 + 阈值滑块 ==========
        hot_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        hot_frame.pack(fill="x", padx=30, pady=(10, 5))

        hot_label = ctk.CTkLabel(
            hot_frame, text=_("toolbox.hotword"), font=(get_font_family(), get_font_size(17)),
            text_color=self.colors.text
        )
        self._title_labels.append(hot_label)
        hot_label.pack(side="left")

        # 从配置读取当前值，默认开启
        hot_enabled = self._config.get("hot_enabled", True) if self._config else True
        self._hot_switch = ctk.CTkCheckBox(
            hot_frame, text="",
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            checkbox_width=24, checkbox_height=24,
            command=self._on_hot_changed
        )
        self._hot_switch.pack(side="right")
        if hot_enabled:
            self._hot_switch.select()
        else:
            self._hot_switch.deselect()

        # 热词阈值滑块行
        threshold_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        threshold_frame.pack(fill="x", padx=30, pady=(0, 5))

        # 从配置读取当前阈值，默认0.85
        hot_threshold = self._config.get("hot_threshold", 0.85) if self._config else 0.85
        # 阈值显示标签
        threshold_text = _("toolbox.threshold_format").replace("{value}", f"{hot_threshold:.2f}")
        self._threshold_label = ctk.CTkLabel(
            threshold_frame, text=threshold_text, font=(get_font_family(), get_font_size(14)),
            text_color=self.colors.text_secondary
        )
        self._threshold_label.pack(side="left", padx=(20, 0))

        # 阈值滑块
        self._threshold_slider = ctk.CTkSlider(
            threshold_frame, from_=0.5, to=1.0,
            width=200, height=16,
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            button_color=self.colors.accent, button_hover_color=self.colors.hover,
            number_of_steps=50,
            command=self._on_threshold_changed
        )
        self._threshold_slider.pack(side="right")
        self._threshold_slider.set(hot_threshold)

        # 编辑热词文件按钮
        edit_hot_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        edit_hot_frame.pack(fill="x", padx=30, pady=(0, 5))

        # 编辑热词文件按钮（存为实例属性以便主题切换时刷新颜色）
        # Edit hotword file button (store as instance attr for theme refresh)
        self._edit_hot_btn = ctk.CTkButton(
            edit_hot_frame, text=_("toolbox.edit_hotword"), font=(get_font_family(), get_font_size(14)),
            fg_color=self.colors.hover, text_color=self.colors.text,
            hover_color=self.colors.active,
            corner_radius=6, height=30,
            command=self._on_edit_hotword_file
        )
        self._edit_hot_btn.pack(side="left", padx=(20, 0))

        # ========== 正则替换开关 ==========
        rule_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        rule_frame.pack(fill="x", padx=30, pady=(10, 5))

        rule_label = ctk.CTkLabel(
            rule_frame, text=_("toolbox.hot_rule"), font=(get_font_family(), get_font_size(17)),
            text_color=self.colors.text
        )
        self._title_labels.append(rule_label)
        rule_label.pack(side="left")

        # 从配置读取当前值，默认开启
        rule_enabled = self._config.get("hot_rule_enabled", True) if self._config else True
        self._rule_switch = ctk.CTkCheckBox(
            rule_frame, text="",
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            checkbox_width=24, checkbox_height=24,
            command=self._on_rule_changed
        )
        self._rule_switch.pack(side="right")
        if rule_enabled:
            self._rule_switch.select()
        else:
            self._rule_switch.deselect()

        # 编辑规则文件按钮
        edit_rule_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        edit_rule_frame.pack(fill="x", padx=30, pady=(0, 5))

        # 编辑规则文件按钮（存为实例属性以便主题切换时刷新颜色）
        # Edit rule file button (store as instance attr for theme refresh)
        self._edit_rule_btn = ctk.CTkButton(
            edit_rule_frame, text=_("toolbox.edit_rule"), font=(get_font_family(), get_font_size(14)),
            fg_color=self.colors.hover, text_color=self.colors.text,
            hover_color=self.colors.active,
            corner_radius=6, height=30,
            command=self._on_edit_rule_file
        )
        self._edit_rule_btn.pack(side="left", padx=(20, 0))

        # ========== 去除语气词开关（从 AI 页移至此处，独立功能不依赖 LLM）==========
        # ========== Remove filler words switch (moved from AI page, independent, no LLM dependency) ==========
        filler_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        filler_frame.pack(fill="x", padx=30, pady=(10, 5))

        filler_label = ctk.CTkLabel(
            filler_frame, text=_("toolbox.remove_filler"), font=(get_font_family(), get_font_size(17)),
            text_color=self.colors.text
        )
        self._title_labels.append(filler_label)
        filler_label.pack(side="left")

        # 从配置读取当前值，默认关闭
        # Read current value from config, default off
        filler_enabled = self._config.get("llm_remove_filler", False) if self._config else False
        self._filler_switch = ctk.CTkCheckBox(
            filler_frame, text="",
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            checkbox_width=24, checkbox_height=24,
            command=self._on_filler_changed
        )
        self._filler_switch.pack(side="right")
        if filler_enabled:
            self._filler_switch.select()
        else:
            self._filler_switch.deselect()

        # ========== 日记归档开关 ==========
        diary_frame = ctk.CTkFrame(page, corner_radius=0, fg_color="transparent")
        diary_frame.pack(fill="x", padx=30, pady=(10, 5))

        diary_label = ctk.CTkLabel(
            diary_frame, text=_("toolbox.diary"), font=(get_font_family(), get_font_size(17)),
            text_color=self.colors.text
        )
        self._title_labels.append(diary_label)
        diary_label.pack(side="left")

        # 从配置读取当前值，默认开启
        diary_enabled = self._config.get("diary_enabled", True) if self._config else True
        self._diary_switch = ctk.CTkCheckBox(
            diary_frame, text="",
            font=(get_font_family(), get_font_size(15)),
            fg_color=self.colors.accent, border_color=self.colors.text_secondary,
            checkmark_color="white", hover_color=self.colors.hover,
            checkbox_width=24, checkbox_height=24,
            command=self._on_diary_changed
        )
        self._diary_switch.pack(side="right")
        if diary_enabled:
            self._diary_switch.select()
        else:
            self._diary_switch.deselect()

        return page
