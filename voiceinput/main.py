# -*- coding: utf-8 -*-
# 语音输入工具主程序 - 整合所有模块
# 负责应用程序的初始化、运行和退出流程
# Voice Input Tool Main Program - Integrates all modules
# Responsible for application initialization, running and exit process

# 导入日志记录库
# Import logging library
import logging
# 导入系统相关功能库
# Import system-related functionality library
import sys
# 导入操作系统接口库（用于os._exit）
# Import operating system interface library (for os._exit)
import os
# 导入时间模块（用于获取当前时间戳）
# Import time module (for getting current timestamp)
import time
# 导入线程库（用于录音状态锁）
# Import threading library (for recording state lock)
import threading

# 性能优化：顶部只保留轻量级导入，重型模块延迟到 run() 内导入
# 这样能减少启动时间，让窗口更快显示
# Performance: only lightweight imports at top, heavy modules deferred to run()
# Reduces startup time, window appears faster

# 从app_utils模块导入辅助函数（日志设置、DPI感知、单实例锁、图标生成）
# Import utility functions from app_utils module (logging setup, DPI awareness, single instance lock, icon generation)
from .app_utils import (
    setup_file_logging,                   # 设置日志文件处理器 / Setup log file handler
    enable_dpi_awareness,                 # 启用DPI感知 / Enable DPI awareness
    acquire_single_instance_lock,         # 获取单实例锁 / Acquire single instance lock
    release_single_instance_lock,         # 释放单实例锁 / Release single instance lock
    load_icon,                            # 加载托盘图标 / Load tray icon
    create_default_icon,                  # 创建默认图标 / Create default icon
    LOG_FILE,                             # 日志文件路径 / Log file path
)
# 从config模块导入加载和保存配置函数
# Import config load and save functions from config module
from .config import load_config
# 从i18n模块导入翻译函数和语言设置函数
# Import translation functions and language setting functions from i18n module
from .i18n import _, set_language

# 以下重型模块延迟导入（在 run() 内），减少启动时间：
# Deferred heavy imports (inside run()) to reduce startup time:
#   keyboard_helper  - 键盘模拟（pywin32 等重型依赖）
#   VoiceInputEngine - 语音引擎（pyaudio/websockets/httpx）
#   HotkeyListener   - 热键监听
#   MainWindow       - GUI 主窗口（customtkinter）
#   TextProcessor    - 文本处理器
#   tray_callbacks   - 托盘回调

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ponytail: 日志设置、DPI感知、单实例锁、图标生成等辅助函数已拆分到app_utils.py
# ponytail: 键盘模拟函数已拆分到keyboard_helper.py


class VoiceInputApp:
    # 语音输入应用程序主类
    # 整合所有模块，管理应用程序的生命周期
    
    def __init__(self, config: dict):
        # 初始化应用程序
        # config: 配置字典
        
        # 保存配置引用
        self.config = config
        # 初始化语音输入引擎为空
        self.engine: "VoiceInputEngine" = None
        # 初始化热键监听器为空
        self.hotkey: "HotkeyListener" = None
        # 初始化主窗口为空
        self.main_window = None
        # 初始化录音状态为False
        self._is_recording = False
        # 录音状态锁（保护 _is_recording/engine 跨线程读写，防止热键连按导致竞态）
        # Recording state lock (protect _is_recording/engine cross-thread read/write, prevent race on rapid hotkey press)
        self._recording_lock = threading.Lock()
        # 初始化托盘图标为空
        self._tray = None
        # 初始化关闭回调函数为空
        self._on_close_callback = None
        # 初始化录音前的活动窗口句柄（用于粘贴后恢复焦点）
        self._prev_active_window = None
        # 初始化窗口显示重试计数器
        self._show_window_retry_count = 0
        # 最大重试次数（10次 * 0.5秒 = 5秒超时）
        self._show_window_max_retries = 10
        # 初始化文本处理器为空（在run()中创建）
        # Initialize text processor to None (created in run())
        self.text_processor: "TextProcessor" = None
        # ponytail: 托盘优先架构 - 启动只创建轻量tk.Tk()root，customtkinter延后到用户点显示才加载
        # 轻量root引用，用于启动期mainloop和托盘点击调度
        self._lightweight_root = None

    def _toggle_recording(self):
        # 切换录音状态
        # 根据当前录音状态决定开始或停止录音
        # 加锁保护，防止热键连按导致 _start/_stop 并发执行
        # Lock protected, prevent concurrent _start/_stop on rapid hotkey press

        with self._recording_lock:
            # 检查是否正在录音
            if self._is_recording:
                # 如果正在录音，调用停止录音函数
                self._stop_recording()
            else:
                # 如果未录音，调用开始录音函数
                self._start_recording()

    def _start_recording(self):
        # 开始录音
        # 创建语音输入引擎实例，设置回调函数，启动引擎

        # 检查是否已在录音中
        if self._is_recording:
            # 记录日志并忽略重复启动
            logger.info("托盘: 录音已在进行中，忽略重复启动")
            return
        # 检查 GUI 是否已初始化（防止热键在 GUI 初始化前触发）
        if self.main_window is None:
            logger.warning("托盘: GUI 尚未初始化，忽略热键触发")
            return
        # 性能优化：首次录音时检查依赖包（启动时跳过，加快启动速度）
        # Performance: check dependencies on first recording (skip at startup, faster startup)
        if not getattr(self, "_deps_checked", False):
            check_dependencies()
            self._deps_checked = True
            logger.info("程序: 依赖检查通过")
        # 检查 AI 配置是否已设置
        api_key = self.config.get("api_key", "").strip()
        base_url = self.config.get("base_url", "").strip()
        access_key = self.config.get("access_key", "").strip()
        if not api_key and not access_key:
            # AI 配置未设置，提示用户
            logger.warning("托盘: AI 配置未设置，请先在设置中配置 API 信息")
            self.main_window.set_status("AI 未设置，请先配置 API")
            self.main_window.update_floating_status("AI 未设置")
            return
        # 记录开始录音日志
        # 添加会话分隔符，便于在日志中区分不同的"录音→识别→输出"循环
        # Add session separator to distinguish different "record→recognize→output" cycles in logs
        # 会话计数器（首次录音时初始化）
        # Session counter (initialized on first recording)
        if not hasattr(self, '_session_count'):
            self._session_count = 0
        self._session_count += 1
        # 使用明显的分隔符，包含会话编号和时间戳，便于排查故障时定位具体哪次循环
        # Use obvious separator with session number and timestamp for troubleshooting
        logger.info("=" * 60)
        logger.info("【录音会话 #%d 开始】 %s", self._session_count, time.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("托盘: 开始录音")
        # 记录当前活动窗口句柄（用于粘贴后恢复焦点）
        try:
            import win32gui
            self._prev_active_window = win32gui.GetForegroundWindow()
            logger.info("托盘: 已记录当前活动窗口句柄: %s", self._prev_active_window)
        except ImportError:
            logger.warning("托盘: pywin32 未安装，无法记录活动窗口")
            self._prev_active_window = None
        except Exception as e:
            logger.warning("托盘: 获取活动窗口失败: %s", e)
            self._prev_active_window = None
        # 设置录音状态为True
        self._is_recording = True
        # 记录创建引擎日志
        logger.info("托盘: 创建 VoiceInputEngine 实例")
        # 延迟导入 VoiceInputEngine（pyaudio/websockets/httpx 较重，首次录音才加载）
        # Deferred import of VoiceInputEngine (pyaudio/websockets/httpx heavy, loaded on first recording)
        from .engine import VoiceInputEngine
        # 创建语音输入引擎实例
        self.engine = VoiceInputEngine(self.config)
        # 记录设置回调日志
        logger.info("托盘: 设置引擎回调函数")
        # 设置引擎回调函数
        self.engine.set_callbacks(
            on_result=self._on_result,      # 识别结果回调
            on_status=self._on_status,      # 状态变更回调
            on_error=self._on_error,        # 错误信息回调
        )
        # 记录启动引擎日志
        logger.info("托盘: 调用 engine.start()")
        # 启动语音输入引擎
        self.engine.start()
        # 记录更新图标日志
        logger.info("托盘: 更新托盘图标")
        # 更新托盘图标状态
        self._update_icon()
        # 更新主窗口状态为"录音中"
        self.main_window.set_status("录音中")
        # 更新悬浮窗状态为"正在录音"
        self.main_window.update_floating_status("正在录音")
        # 根据悬浮窗功能状态决定显示哪个窗口
        if self.main_window._floating_enabled:
            # 如果悬浮窗功能开启，只显示悬浮窗
            if self.main_window.floating_window:
                self.main_window.floating_window.show()
                logger.info("托盘: 悬浮窗已显示")
        else:
            # 如果悬浮窗功能关闭，显示主窗口
            self.main_window.bring_to_front()
            logger.info("托盘: 主窗口已显示")
        # 记录录音已启动日志
        logger.info("托盘: 录音已启动")

    def _stop_recording(self):
        # 停止录音
        # 停止语音输入引擎，更新界面状态
        
        # 检查是否未在进行录音
        if not self._is_recording:
            # 记录日志并忽略停止请求
            logger.info("托盘: 录音未在进行中，忽略停止请求")
            return
        # 记录停止录音日志
        logger.info("托盘: 停止录音")
        # 更新主窗口状态为"识别中，请稍候..."
        self.main_window.set_status("识别中，请稍候...")
        # 更新悬浮窗状态为"正在识别"
        self.main_window.update_floating_status("正在识别")
        # 设置录音状态为False
        self._is_recording = False
        # 检查引擎实例是否存在
        if self.engine:
            # 记录调用引擎停止日志
            logger.info("托盘: 调用 engine.stop()")
            # 停止语音输入引擎
            self.engine.stop()
            # 记录引擎已停止日志
            logger.info("托盘: 引擎已停止")
            # 清空引擎实例引用
            self.engine = None
        # 记录更新图标日志
        logger.info("托盘: 更新托盘图标")
        # 更新托盘图标状态
        self._update_icon()
        # 更新主窗口状态为"识别已完成"
        self.main_window.set_status("识别已完成")
        # 更新悬浮窗状态为"识别完成"
        self.main_window.update_floating_status("识别完成")
        # 记录本次录音结束分隔线
        # Log end separator for this recording session
        logger.info("-" * 60)

    def _on_result(self, text: str, is_final: bool):
        # 处理语音识别结果
        # text: 识别到的文本
        # is_final: 是否为最终结果
        # Handle speech recognition result
        # text: recognized text
        # is_final: whether it's the final result

        # 检查是否为最终结果且文本非空
        # Check if it's the final result and text is not empty
        if is_final and text.strip():
            # 记录收到最终识别结果日志
            # Log received final recognition result
            logger.info("托盘: 收到最终识别结果: %s", text.strip())

            # 使用文本处理器进行后处理
            # Use text processor for post-processing
            processed_text = text.strip()
            if self.text_processor:
                # 调用文本处理管线，传入LLM回调函数
                # Call text processing pipeline, pass LLM callback
                processed_text = self.text_processor.process(
                    processed_text,
                    llm_callback=self._on_llm_result,
                )

            # 如果处理后文本非空（LLM处理时可能返回空字符串）
            # If processed text is not empty (LLM processing may return empty string)
            if processed_text:
                # 检测动态口令控制字符串
                # Detect dynamic command control strings
                if processed_text == "__UNDO__":
                    # 撤销：模拟 Ctrl+Z
                    # Undo: simulate Ctrl+Z
                    logger.info("口令: 执行撤销操作")
                    self._keyboard_helper.simulate_undo(self._prev_active_window)
                    return
                elif processed_text == "__NEWLINE__":
                    # 换行：模拟 Enter 键
                    # Newline: simulate Enter key
                    logger.info("口令: 执行换行操作")
                    self._keyboard_helper.simulate_enter(self._prev_active_window)
                    return
                elif processed_text == "__BACKSPACE__":
                    # 退格：模拟 Backspace 键
                    # Backspace: simulate Backspace key
                    logger.info("口令: 执行退格操作")
                    self._keyboard_helper.simulate_backspace(self._prev_active_window)
                    return
                # 保存最近一次识别结果（用于复制）
                # Save most recent recognition result (for copying)
                if self.text_processor:
                    self.text_processor.set_last_result(processed_text)
                # 将识别文本追加到主窗口
                # Append recognized text to main window
                self.main_window.append_text(processed_text)
                # 更新悬浮窗识别结果
                # Update floating window recognition result
                self.main_window.update_floating_result(processed_text)
                # 自动保存到历史记录
                # Auto save to history
                self.main_window.append_to_history(processed_text)
                # 只有悬浮窗开启时，才自动复制到剪贴板并粘贴到光标位置
                # Only auto copy and paste when floating window is enabled
                if self.main_window._floating_enabled:
                    try:
                        self.main_window.copy_to_clipboard(processed_text)
                        logger.info("托盘: 结果已复制到剪贴板")
                        # 模拟 Ctrl+V 粘贴到光标位置
                        # Simulate Ctrl+V paste to cursor position
                        self._keyboard_helper.paste_to_cursor(self._prev_active_window)
                        logger.info("托盘: 结果已粘贴到光标位置")
                    except Exception as e:
                        logger.warning("托盘: 复制或粘贴失败: %s", e)
                # 识别完成后，自动隐藏主窗口和悬浮窗，回到刚启动的状态
                # After recognition, auto hide main window and floating window
                self._hide_windows_after_recognition()
        else:
            # 记录收到中间识别结果日志
            # Log received intermediate recognition result
            logger.debug("托盘: 收到中间识别结果: %s", text)
            # 更新主窗口文本（不追加）
            # Update main window text (no append)
            self.main_window.update_text(text)

    def _on_llm_result(self, result_text: str, is_final: bool):
        # 处理LLM角色返回的结果
        # result_text: LLM返回的文本
        # is_final: 是否为最终结果
        # Handle LLM role returned result
        # result_text: LLM returned text
        # is_final: whether it's the final result

        # 检查结果是否非空
        # Check if result is not empty
        if result_text and is_final:
            # 记录LLM结果日志
            # Log LLM result
            logger.info("托盘: 收到LLM结果: %s", result_text[:50])
            # 保存最近一次识别结果
            # Save most recent recognition result
            if self.text_processor:
                self.text_processor.set_last_result(result_text)
            # 将LLM结果追加到主窗口
            # Append LLM result to main window
            self.main_window.append_text(result_text)
            # 更新悬浮窗识别结果
            # Update floating window recognition result
            self.main_window.update_floating_result(result_text)
            # 自动保存到历史记录
            # Auto save to history
            self.main_window.append_to_history(result_text)
            # 只有悬浮窗开启时，才自动复制到剪贴板并粘贴到光标位置
            # Only auto copy and paste when floating window is enabled
            if self.main_window._floating_enabled:
                try:
                    self.main_window.copy_to_clipboard(result_text)
                    logger.info("托盘: LLM结果已复制到剪贴板")
                    # 模拟 Ctrl+V 粘贴到光标位置
                    # Simulate Ctrl+V paste to cursor position
                    self._keyboard_helper.paste_to_cursor(self._prev_active_window)
                    logger.info("托盘: LLM结果已粘贴到光标位置")
                except Exception as e:
                    logger.warning("托盘: LLM结果复制或粘贴失败: %s", e)
            # 识别完成后，自动隐藏主窗口和悬浮窗
            # After recognition, auto hide main window and floating window
            self._hide_windows_after_recognition()

    def _on_status(self, status: str):
        # 处理状态变更
        # status: 新的状态字符串
        # 引擎回调线程调用，修改 _is_recording 需加锁保护
        # Called by engine callback thread, lock _is_recording modification

        # 记录状态变更日志
        logger.info("状态变更: %s", status)
        # 检查是否为错误状态
        if status == "error":
            # 加锁修改录音状态
            # Lock protected recording state modification
            with self._recording_lock:
                self._is_recording = False
            # 更新托盘图标状态
            self._update_icon()
            # 更新主窗口状态为错误提示（通过翻译函数获取）
            self.main_window.set_status(_("status.connection_error"))
        elif status == "timeout":
            # 录音超时自动停止：引擎已停止录音，正在识别
            # 设置 _is_recording = False，防止用户按键时重复停止
            # Recording timeout auto-stop: engine stopped recording, recognizing
            # Set _is_recording = False to prevent duplicate stop on user keypress
            with self._recording_lock:
                self._is_recording = False
            # 更新托盘图标状态（恢复为非录音状态）
            # Update tray icon (restore to non-recording state)
            self._update_icon()
            # 更新 UI 状态为"录音超时，正在识别..."
            # Update UI status to "recording timeout, recognizing..."
            self.main_window.set_status("录音超时，正在识别...")
            self.main_window.update_floating_status("超时识别中")

    def _on_error(self, error_msg: str):
        # 处理错误信息
        # error_msg: 错误信息字符串
        
        # 记录收到错误信息日志（错误应使用error级别）
        # Log error message (errors should use error level)
        logger.error("托盘: 收到错误信息: %s", error_msg)
        # 更新主窗口状态为错误信息（通过翻译函数获取）
        self.main_window.set_status(f"{_('status.error_prefix')}: {error_msg}")

    # ponytail: _restore_focus/_paste_to_cursor/_simulate_* 已拆分到keyboard_helper.py
    # 调用时通过 keyboard_helper.xxx(self._prev_active_window) 方式使用

    def _ensure_autostart(self):
        # 检查开机自启动是否已注册，未注册则创建
        # 三级检查：注册表 Run 键 > 快捷方式 .lnk > .bat 脚本
        # 确保配置中 autostart=True 时，至少有一种方式生效
        # Check if auto-start is registered, create if not
        # Three-tier check: registry Run key > shortcut .lnk > .bat script
        # Ensure at least one method works when autostart=True in config
        import os
        # 方案1：检查注册表 Run 键（主流方案）
        # Tier 1: check registry Run key (mainstream)
        from .autostart_helper import is_registered as registry_is_registered, set_autostart as registry_set_autostart, get_command as registry_get_command
        if registry_is_registered():
            # 注册表已注册，无需其他方案
            # Registry registered, no need for other methods
            return
        # 方案2和3：检查快捷方式和.bat脚本
        # Tier 2 and 3: check shortcut and .bat script
        # 获取 Windows 启动目录路径
        # Get Windows Startup folder path
        startup_folder = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )
        # 检查快捷方式和备用脚本是否都存在
        # Check if both shortcut and fallback script exist
        shortcut_path = os.path.join(startup_folder, "VoiceInput.lnk")
        bat_path = os.path.join(startup_folder, "VoiceInput.bat")
        # 如果任一存在，说明已注册开机启动
        # If either exists, auto-start is already registered
        if os.path.exists(shortcut_path) or os.path.exists(bat_path):
            return
        # 都不存在，需要创建
        # Neither exists, need to create
        logger.info("开机启动: 配置已启用但未注册，正在创建...")
        # 委托给 GUI 的 _set_autostart 方法创建（会优先尝试注册表）
        # Delegate to GUI's _set_autostart method (will try registry first)
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window._set_autostart(True)
        else:
            # GUI 还没初始化，直接用注册表方案创建
            # GUI not initialized yet, use registry directly
            if not registry_set_autostart(registry_get_command()):
                # 注册表失败，回退到 .bat 方案
                # Registry failed, fallback to .bat
                import sys
                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                try:
                    with open(bat_path, "w", encoding="utf-8") as f:
                        f.write('@echo off\n')
                        f.write(f'cd /d "{project_dir}"\n')
                        f.write(f'"{sys.executable}" "{os.path.join(project_dir, "voiceinput", "__main__.py")}"\n')
                    logger.info("开机启动: 已创建启动脚本 '%s'", bat_path)
                except Exception as e:
                    logger.error("开机启动: 创建启动脚本失败: %s", e)

    def _hide_windows_after_recognition(self):
        # 识别完成后隐藏窗口
        # 根据配置决定隐藏主窗口还是悬浮窗
        
        # 检查悬浮窗功能是否开启
        if self.main_window._floating_enabled:
            # 如果悬浮窗功能开启，隐藏悬浮窗
            if self.main_window.floating_window:
                self.main_window.floating_window.hide()
                logger.info("托盘: 悬浮窗已隐藏")
        else:
            # 如果悬浮窗功能关闭，隐藏主窗口
            self.main_window.hide()
            logger.info("托盘: 主窗口已隐藏")

    def _update_icon(self):
        # 更新托盘图标状态
        # 根据录音状态更新图标颜色和提示文字
        
        # 检查托盘实例是否存在
        if self._tray:
            try:
                # 根据录音状态加载相应图标
                icon = load_icon(recording=self._is_recording)
                # 根据录音状态构建提示文字（通过翻译函数获取）
                title = _("tray.recording") if self._is_recording else _("tray.ready")
                # 更新托盘图标和提示文字
                self._tray.update_icon(icon=icon, title=title)
            except Exception as e:
                # 记录更新图标失败日志
                logger.error("更新图标失败: %s", e)

    def _quit(self):
        # 退出程序
        # 停止所有模块，清理资源
        
        # 记录开始退出日志
        logger.info("程序: 开始退出流程")
        # 停止录音（如果正在录音）
        self._stop_recording()
        # 检查热键监听器是否存在
        if self.hotkey:
            # 停止热键监听
            self.hotkey.stop()
        # 检查托盘实例是否存在
        if self._tray:
            try:
                # 停止托盘图标（设置_running=False并立即删除图标）
                self._tray.stop()
            except Exception as e:
                logger.debug("退出: 停止托盘异常: %s", e)
        # 检查主窗口是否存在
        if self.main_window:
            try:
                # 先停止 tkinter 主循环
                self.main_window._root.quit()
            except Exception as e:
                logger.debug("退出: 停止tkinter循环异常: %s", e)
            try:
                # 销毁主窗口
                self.main_window._root.destroy()
            except Exception as e:
                logger.debug("退出: 销毁窗口异常: %s", e)
        # 退出时清空历史记录文件
        from .config import clear_history
        clear_history()
        # 检查关闭回调函数是否存在
        if self._on_close_callback:
            # 调用关闭回调函数
            self._on_close_callback()
        # 释放单实例锁文件
        # Release single instance lock file
        release_single_instance_lock()
        # 记录退出完成日志
        logger.info("程序: 退出流程完成")
        # 手动刷新所有日志处理器，确保日志落盘（os._exit 不执行 finally/atexit）
        # Manually flush all log handlers to persist logs (os._exit skips finally/atexit)
        for handler in logging.getLogger().handlers:
            try:
                handler.flush()
            except Exception:
                pass
        # 终止程序进程
        # 使用 os._exit 而非 sys.exit：keyboard 库的监听线程是非守护线程，
        # sys.exit 会等待它结束导致卡住；os._exit 立即终止，但已手动 flush 日志
        # Use os._exit instead of sys.exit: keyboard lib's listener thread is non-daemon,
        # sys.exit would wait for it and hang; os._exit terminates immediately, logs already flushed
        os._exit(0)

    def run(self):
        # 运行应用程序
        # 启动所有模块，进入主事件循环
        # Run application
        # Start all modules, enter main event loop

        # 性能优化：重型模块延迟导入（启动时才加载，减少首次显示时间）
        # Performance: deferred import of heavy modules (loaded on startup, reduces first display time)
        # VoiceInputEngine 和 MainWindow 在使用处（_start_recording/_init_gui）再延迟导入
        # VoiceInputEngine and MainWindow are further deferred to usage point (_start_recording/_init_gui)
        from . import keyboard_helper
        from .text_processor import TextProcessor
        from .tray_callbacks import add_hotword, copy_result, clear_llm_history
        from .tray_icon import TrayIcon
        # 保存到实例属性，供其他方法使用
        # Save to instance attributes for use in other methods
        self._keyboard_helper = keyboard_helper
        self._tray_callbacks = (add_hotword, copy_result, clear_llm_history)

        # 创建文本处理器实例
        # Create text processor instance
        logger.info("托盘: 创建 TextProcessor 实例")
        self.text_processor = TextProcessor(self.config)
        logger.info("托盘: 文本处理器已创建")

        # 检查开机自启动配置，如果启用但快捷方式不存在则自动创建
        # Check auto-start config, if enabled but shortcut doesn't exist, create it
        if self.config.get("autostart", False):
            self._ensure_autostart()

        # 记录创建热键监听器日志
        logger.info("托盘: 创建 HotkeyListener 实例")
        # 从配置读取热键组合（默认 ctrl+alt），解析为虚拟键码列表
        # Read hotkey combo from config (default ctrl+alt), parse to virtual key code list
        from .hotkey import HotkeyListener, parse_hotkey
        hotkey_combo = self.config.get("hotkey_combo", "ctrl+alt")
        vkeys = parse_hotkey(hotkey_combo)
        logger.info("托盘: 热键组合: %s (vkeys=%s)", hotkey_combo, [hex(k) for k in vkeys])
        # 创建热键监听器实例，传入用户自定义的虚拟键码列表（支持 1-3 键）
        # Create hotkey listener instance with user's custom virtual key code list (1-3 keys)
        self.hotkey = HotkeyListener(
            on_toggle=self._toggle_recording,  # 热键触发时切换录音状态
            vkeys=vkeys,
        )
        # 记录启动热键日志
        logger.info("托盘: 启动热键监听")
        # 启动热键监听
        self.hotkey.start()
        # 记录热键已启动日志
        logger.info("托盘: 热键监听已启动")

        # 记录加载图标日志
        logger.info("托盘: 加载托盘图标")
        # 加载托盘图标（如果失败则创建默认图标）
        icon = load_icon(recording=False) or create_default_icon()
        # 记录图标已加载日志
        logger.info("托盘: 托盘图标已加载")

        # 记录创建托盘日志
        logger.info("托盘: 创建 win32gui 托盘实例")
        # 创建托盘图标实例（通过翻译函数获取提示文字）
        # Create tray icon instance (via translation function for tooltip text)
        self._tray = TrayIcon(
            title=_("tray.ready"),                          # 托盘提示文字
            on_left_click=self._show_window,                # 左键点击显示窗口
            on_quit=self._quit,                             # 退出时调用_quit
            on_add_hotword=self._add_hotword,               # 添加热词回调
            on_copy_result=self._copy_result,               # 复制结果回调
            on_clear_llm_history=self._clear_llm_history,  # 清除LLM记忆回调
        )
        # 记录托盘已创建日志
        logger.info("托盘: 托盘实例已创建")

        # 记录启动托盘日志
        logger.info("托盘: 在后台线程启动托盘事件循环")
        # 导入多线程支持库
        import threading
        # 创建后台线程运行托盘事件循环
        tray_thread = threading.Thread(target=lambda: self._tray.run(icon), daemon=True)
        # 启动托盘线程
        tray_thread.start()
        # 记录托盘已启动日志
        logger.info("托盘: 托盘事件循环已启动")

        # 记录启动GUI日志
        logger.info("GUI: 启动 tkinter 事件循环")
        # 调用GUI运行函数
        run_gui_app(self)

    def _close_main_window(self):
        # 关闭主窗口（销毁窗口但保留托盘）
        # 托盘图标保持不变，点击托盘可重新打开窗口
        if self.main_window:
            self.main_window.close()
            logger.info("托盘: 主窗口已关闭")

    def _show_window(self):
        # 显示主窗口
        # 托盘左键点击时调用
        # 注意：此方法在后台线程中被调用，需要确保 UI 操作在主线程执行
        
        # 记录显示窗口日志
        logger.info("托盘: 左键点击，显示窗口")
        
        # 尝试获取 tkinter root 用于线程调度
        root = None
        if self.main_window is not None:
            try:
                # 检查 _root 是否存在
                if hasattr(self.main_window, '_root') and self.main_window._root is not None:
                    if self.main_window._root.winfo_exists():
                        root = self.main_window._root
            except Exception as e:
                logger.debug("显示窗口: root检查异常: %s", e)
                root = None

        if root is not None:
            # 主窗口存在，调度到主线程显示
            # 重置重试计数器（GUI 已准备好）
            self._show_window_retry_count = 0
            root.after(0, self._show_window_in_main_thread)
        elif self._lightweight_root is not None:
            # ponytail: 托盘优先架构 - 主窗口未创建，用轻量root调度_recreate创建主窗口
            try:
                if self._lightweight_root.winfo_exists():
                    # 轻量root可用，调度到主线程创建主窗口
                    self._show_window_retry_count = 0
                    self._lightweight_root.after(0, self._show_window_in_main_thread)
                else:
                    raise Exception("lightweight root destroyed")
            except Exception as e:
                logger.debug("显示窗口: 轻量root异常: %s", e)
                import threading
                self._show_window_retry_count += 1
                if self._show_window_retry_count >= self._show_window_max_retries:
                    logger.error("托盘: GUI 初始化超时（%d 次重试），停止显示窗口", self._show_window_retry_count)
                    self._show_window_retry_count = 0
                    return
                threading.Timer(0.5, self._show_window).start()
        else:
            # 没有任何 root，说明 GUI 尚未初始化
            # 这种情况可能发生，因为托盘在后台线程启动，而 GUI 在主线程初始化
            # 检查是否超过最大重试次数
            self._show_window_retry_count += 1
            if self._show_window_retry_count >= self._show_window_max_retries:
                # 超过最大重试次数，停止重试
                logger.error("托盘: GUI 初始化超时（%d 次重试），停止显示窗口", self._show_window_retry_count)
                self._show_window_retry_count = 0
                return
            # 等待后重试
            logger.warning("托盘: GUI 尚未初始化，等待后重试 (第 %d/%d 次)",
                          self._show_window_retry_count, self._show_window_max_retries)
            import threading
            threading.Timer(0.5, self._show_window).start()

    def _show_window_in_main_thread(self):
        # 在主线程中显示或重新创建主窗口
        # 此方法由 _show_window 通过 after() 调度到主线程执行
        logger.info("托盘: 在主线程中处理窗口显示请求")
        
        if self.main_window is None or not self.main_window._root.winfo_exists():
            # 窗口不存在，重新创建
            self._recreate_main_window()
        else:
            self.main_window.bring_to_front()

    def _recreate_main_window(self):
        # 重新创建主窗口
        # ponytail: 托盘优先架构 - 销毁轻量root，创建MainWindow(CTk)并启动新mainloop
        # 此方法在轻量root的after回调中调用，新mainloop嵌套运行（仅首次显示发生一次）
        # 此方法必须在主线程中调用
        logger.info("托盘: 重新创建主窗口")
        try:
            # 销毁轻量root（退出启动期mainloop，为创建CTk root让路，tkinter只能有一个主root）
            if self._lightweight_root is not None:
                self._lightweight_root.destroy()
                self._lightweight_root = None
            # 延迟导入 MainWindow（customtkinter 较重，首次加载~2秒）
            # Deferred import of MainWindow (customtkinter is heavy)
            from .gui import MainWindow
            self.main_window = MainWindow(self.config)
            self.main_window.set_config(self.config)
            self.main_window.load_theme_from_config(self.config)
            self.main_window.set_on_close_callback(self._close_main_window)
            # 把热键监听器的暂停/恢复方法传给主窗口
            # 用于设置页捕获热键时暂停全局热键监听，避免冲突触发录音
            if hasattr(self, 'hotkey') and self.hotkey:
                self.main_window.set_hotkey_callbacks(self.hotkey.pause, self.hotkey.resume)
            self.main_window.bring_to_front()
            logger.info("托盘: 主窗口重新创建成功")
            # 启动主窗口mainloop（嵌套在轻量root的after回调里，主窗口一直活直到程序退出）
            self.main_window.mainloop()
        except Exception as e:
            logger.error("托盘: 重新创建主窗口失败: %s", e)

    def _add_hotword(self):
        # 添加热词（委托给tray_callbacks模块处理）
        # Add hotword (delegate to tray_callbacks module)
        # tray_callbacks 在 run() 中延迟导入并保存到 self._tray_callbacks
        # tray_callbacks is deferred imported in run() and saved to self._tray_callbacks
        add_hotword, _, _ = self._tray_callbacks
        add_hotword(self.text_processor)

    def _copy_result(self):
        # 复制最近一次识别结果到剪贴板（委托给tray_callbacks模块处理）
        # Copy most recent result to clipboard (delegate to tray_callbacks module)
        _, copy_result, _ = self._tray_callbacks
        copy_result(self.text_processor)

    def _clear_llm_history(self):
        # 清除LLM对话记忆（委托给tray_callbacks模块处理）
        # Clear LLM conversation history (delegate to tray_callbacks module)
        _, _, clear_llm_history = self._tray_callbacks
        clear_llm_history(self.text_processor)


def run_gui_app(app_instance):
    # 运行GUI应用程序
    # ponytail: 托盘优先架构 - 启动只创建轻量tk.Tk()root，customtkinter延后到用户点显示才加载
    # 启动期只加载标准库tkinter（快），customtkinter（重~2秒）延后到_recreate_main_window首次调用
    # app_instance: VoiceInputApp实例

    # 导入标准库tkinter（轻量，不触发customtkinter加载）
    import tkinter as tk
    # 创建轻量root作为启动期mainloop载体（用户不可见）
    app_instance._lightweight_root = tk.Tk()
    # 隐藏轻量root（用户不感知，仅作mainloop和托盘点击调度用）
    app_instance._lightweight_root.withdraw()
    # 启动轻量root的mainloop，等待托盘点击触发_recreate_main_window创建主窗口
    app_instance._lightweight_root.mainloop()


def check_dependencies():
    # 检查程序依赖包
    # 验证所有必需的第三方库是否已安装
    # 如果有缺失的包，打印提示信息并退出程序
    # Check program dependencies
    # Verify all required third-party libraries are installed
    # If any are missing, print message and exit

    # ponytail: 循环替代5个重复的try-except
    # 必需模块列表：(模块名, pip包名)
    required = [
        ("pyaudio", "pyaudio"),
        ("websockets", "websockets"),
        ("win32gui", "pywin32"),
        ("PIL", "Pillow"),
        ("httpx", "httpx"),
    ]
    missing = []
    for module_name, package_name in required:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    # 检查是否有缺失的包
    if missing:
        print(f"缺少依赖包: {', '.join(missing)}")
        print(f"请运行: pip install {' '.join(missing)}")
        # 退出程序
        sys.exit(1)


def main():
    # 程序入口函数
    # 初始化程序，加载配置，启动应用程序
    
    # 设置日志文件处理器（在记录任何日志之前）
    # Setup log file handler (before logging any messages)
    setup_file_logging()
    
    # 记录程序启动日志
    logger.info("程序: 启动语音输入工具")
    # 记录日志文件路径
    # Log log file path
    logger.info("程序: 日志文件路径: %s", LOG_FILE)
    # 启用Windows DPI感知
    enable_dpi_awareness()
    # 记录DPI感知已启用日志
    logger.info("程序: DPI 感知已启用")
    
    # 尝试获取单实例锁
    if not acquire_single_instance_lock():
        # 如果获取锁失败，记录警告日志
        logger.warning("程序: 检测到已有实例在运行，退出")
        # 打印提示信息（通过翻译函数获取）
        print(_("app.title") + " " + "已在运行中，请勿重复启动")
        # 退出程序
        sys.exit(1)
    # 记录单实例锁已获取日志
    logger.info("程序: 单实例锁已获取")

    # 性能优化：依赖检查延迟到首次录音时执行（check_dependencies）
    # 这样启动时不需要导入 5 个第三方库，加快启动速度
    # Performance: dependency check deferred to first recording (check_dependencies)
    # This avoids importing 5 third-party libraries at startup, speeds up startup

    # 记录加载配置日志
    logger.info("程序: 加载配置")
    # 加载配置文件
    config = load_config()
    # 记录配置加载完成日志
    logger.info("程序: 配置加载完成")

    # 从配置中加载界面语言设置
    # Load interface language setting from config
    lang = config.get("language", "en")
    # 设置当前语言
    # Set current language
    set_language(lang)
    # 记录语言设置加载日志
    # Log language setting loaded
    logger.info("程序: 界面语言已设置为: %s", lang)

    # 检查API配置是否缺失
    if not config.get("api_key") and not config.get("access_key"):
        # 记录显示首次使用提示日志
        logger.info("程序: 检测到API配置缺失，显示首次使用提示")
        # 打印配置提示框
        print("=" * 50)
        print("  语音输入工具 - 首次使用配置")
        print("=" * 50)
        print()
        print("  请先在系统托盘右键图标 -> 设置 中配置:")
        print("  - API 地址 (Base URL)")
        print("  - API 密钥 (API Key)")
        print("  - 模型名称 (Model)")
        print()
        print("  示例:")
        print("  - 百炼: https://dashscope.aliyuncs.com/compatible-mode")
        print("  - OpenAI: https://api.openai.com/v1")
        print("=" * 50)
    else:
        # 记录API密钥已配置日志
        logger.info("程序: API密钥已配置")

    # 记录创建应用程序实例日志
    logger.info("程序: 创建 VoiceInputApp 实例")
    # 创建语音输入应用程序实例
    app = VoiceInputApp(config)
    # 记录运行应用程序日志
    logger.info("程序: 运行应用程序")
    # 运行应用程序
    app.run()


# 程序入口点
if __name__ == "__main__":
    # 调用主函数
    main()
