# -*- coding: utf-8 -*-
# 热键监听模块 - 使用轮询方式检测Ctrl+Alt组合键
# 按一次Ctrl+Alt开始录音，再按一次停止录音
# Hotkey listening module - uses polling to detect Ctrl+Alt key combination
# Press Ctrl+Alt once to start recording, press again to stop recording

# 导入Windows系统API调用库
# Import Windows system API library
import ctypes
# 导入日志记录库
# Import logging library
import logging
# 导入多线程支持库
# Import threading support library
import threading
# 导入时间处理库
# Import time processing library
import time

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# 虚拟键码映射表：键名 -> Windows 虚拟键码
# Virtual key code mapping: key name -> Windows virtual key code
# 包含修饰键、字母键、数字键、功能键，供用户自由组合
# Includes modifier keys, letter keys, number keys, function keys for free combination
VK_MAP = {
    # 修饰键
    # Modifier keys
    "ctrl": 0x11,   # Ctrl 键
    "alt": 0x12,    # Alt 键
    "shift": 0x10,  # Shift 键
    "win": 0x5B,    # 左 Win 键
    # 空格和回车
    # Space and Enter
    "space": 0x20,  # 空格键
    "enter": 0x0D,  # 回车键
    # 字母键 a-z（虚拟键码 0x41-0x5A，键名用小写匹配 parse_hotkey 的 lower() 转换）
    # Letter keys a-z (virtual key codes 0x41-0x5A, lowercase names to match parse_hotkey's lower())
    **{chr(c).lower(): c for c in range(0x41, 0x5B)},
    # 数字键 0-9（虚拟键码 0x30-0x39）
    # Number keys 0-9 (virtual key codes 0x30-0x39)
    **{chr(c): c for c in range(0x30, 0x3A)},
    # 功能键 F1-F12（虚拟键码 0x70-0x7B）
    # Function keys F1-F12 (virtual key codes 0x70-0x7B)
    **{f"f{i}": 0x6F + i for i in range(1, 13)},
}

# 预定义热键组合（供界面下拉框参考，用户也可自由输入）
# Predefined hotkey combos (for dropdown reference, users can also type freely)
HOTKEY_COMBOS = [
    "ctrl+alt",       # Ctrl+Alt（默认）
    "ctrl+shift",     # Ctrl+Shift
    "alt+shift",      # Alt+Shift
    "ctrl+space",     # Ctrl+空格
    "alt+space",      # Alt+空格
    "ctrl+v",         # Ctrl+V
    "ctrl+s",         # Ctrl+S
    "alt+v",          # Alt+V
    "ctrl+f1",        # Ctrl+F1
    "alt+f2",         # Alt+F2
]


def parse_hotkey(combo_str: str):
    # 将热键组合字符串解析为虚拟键码列表
    # 支持格式：1-3 个键名用 + 连接，如 "f1"、"ctrl+alt"、"ctrl+shift+v"
    # 键名不区分大小写，自动转小写匹配 VK_MAP
    # combo_str: 热键组合字符串，如 "ctrl+alt"
    # 返回: 虚拟键码列表（长度 1-3），解析失败返回默认值 [0x11, 0x12]
    # Parse hotkey combo string to virtual key code list
    # Supports 1-3 key names joined by +, e.g. "f1", "ctrl+alt", "ctrl+shift+v"
    # Key names are case-insensitive, auto lowercased to match VK_MAP
    # combo_str: combo string like "ctrl+alt"
    # Returns: vk list (length 1-3), default [0x11, 0x12] on parse failure
    if not combo_str:
        return [0x11, 0x12]
    # 转小写并按 + 分割
    # Convert to lowercase and split by +
    parts = combo_str.lower().split("+")
    # 逐个从映射表获取虚拟键码
    # Get virtual key code for each part from mapping
    vkeys = []
    for p in parts:
        vk = VK_MAP.get(p.strip())
        # 任一键名无效则返回默认值
        # Return default if any key name invalid
        if vk is None:
            return [0x11, 0x12]
        vkeys.append(vk)
    # 键数必须为 1-3 个
    # Key count must be 1-3
    if not vkeys or len(vkeys) > 3:
        return [0x11, 0x12]
    return vkeys


class HotkeyListener:
    # 热键监听类 - 检测键盘组合键
    # 使用轮询方式持续检测Ctrl+Alt组合键的按下状态
    # Hotkey listening class - detect keyboard key combinations
    # Uses polling to continuously detect Ctrl+Alt key combination press state
    
    def __init__(self, on_toggle, vkeys=None):
        # 初始化热键监听器
        # on_toggle: 热键触发时的回调函数
        # vkeys: 虚拟键码列表（1-3 个），默认 [Ctrl, Alt]
        # Initialize hotkey listener
        # on_toggle: callback function when hotkey triggered
        # vkeys: virtual key code list (1-3 keys), default [Ctrl, Alt]

        # 保存热键触发时的回调函数
        # Save callback function when hotkey triggered
        self.on_toggle = on_toggle
        # 保存虚拟键码列表（支持单键/双键/三键组合）
        # Save virtual key code list (supports 1-3 key combo)
        if vkeys is None:
            vkeys = [0x11, 0x12]
        self.vkeys = list(vkeys)
        # 初始化上一次按键状态为False（未按下）
        # Initialize last key state to False (not pressed)
        self._last_key_state = False
        # 初始化运行状态为False
        # Initialize running state to False
        self._running = False
        # 初始化监听线程为空
        # Initialize listening thread to None
        self._thread = None
        # 暂停标志：True时热键监听不触发回调（用于设置页捕获热键时避免冲突）
        # Pause flag: when True, hotkey listener won't trigger callback (used when capturing hotkey in settings page)
        self._paused = False

    def pause(self):
        # 暂停热键监听（不触发回调，但监听线程仍在运行）
        # Pause hotkey listening (no callback, but listening thread still running)
        self._paused = True
        logger.info("热键: 监听已暂停")

    def resume(self):
        # 恢复热键监听
        # Resume hotkey listening
        self._paused = False
        # 重置上一次按键状态，避免恢复时误触发
        # Reset last key state to avoid false trigger on resume
        self._last_key_state = False
        logger.info("热键: 监听已恢复")

    def start(self):
        # 启动热键监听
        # 创建并启动监听线程，开始轮询检测按键
        # Start hotkey listening
        # Create and start listening thread, begin polling to detect key presses
        
        # 检查热键监听是否已在运行
        # Check if hotkey listening is already running
        if self._running:
            # 记录警告日志并忽略重复启动
            # Log warning and ignore duplicate start
            logger.info("热键: 热键监听已在运行中，忽略重复启动")
            return
        # 设置运行状态为True
        # Set running state to True
        self._running = True
        # 记录创建线程日志
        # Log creating thread
        logger.info("热键: 创建热键监听线程")
        # 创建监听线程，目标函数为_listen_loop，设置为守护线程
        # Create listening thread, target function is _listen_loop, set as daemon thread
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        # 启动线程
        # Start thread
        self._thread.start()
        # 记录热键监听已启动日志
        # Log hotkey listening started
        logger.info("热键: 热键监听已启动 (%d 键组合触发)", len(self.vkeys))

    def stop(self):
        # 停止热键监听
        # 设置运行状态为False，等待线程结束
        # Stop hotkey listening
        # Set running state to False, wait for thread to end
        
        # 记录正在停止日志
        # Log stopping
        logger.info("热键: 正在停止热键监听...")
        # 设置运行状态为False，使监听循环退出
        # Set running state to False, make listening loop exit
        self._running = False
        # 检查监听线程是否存在
        # Check if listening thread exists
        if self._thread:
            # 记录等待线程结束日志
            # Log waiting for thread to end
            logger.info("热键: 等待热键监听线程结束...")
            # 等待线程结束，超时时间3秒
            # Wait for thread to end, timeout 3 seconds
            self._thread.join(timeout=3)
            # 检查线程是否已结束
            # Check if thread has ended
            if not self._thread.is_alive():
                # 记录线程已结束日志
                # Log thread has ended
                logger.info("热键: 热键监听线程已结束")
            else:
                # 记录线程超时警告
                # Log thread timeout warning
                logger.warning("热键: 热键监听线程超时")
        # 记录热键监听已停止日志
        # Log hotkey listening stopped
        logger.info("热键: 热键监听已停止")

    def _listen_loop(self):
        # 监听循环 - 轮询检测按键状态
        # 持续检查配置的所有键是否同时按下，检测到组合键按下时触发回调
        # Listening loop - poll to detect key state
        # Continuously check if all configured keys are pressed, trigger callback when combo pressed

        try:
            # 获取Windows user32.dll库引用
            # Get Windows user32.dll library reference
            user32 = ctypes.windll.user32
            # 记录监听循环开始日志
            # Log listening loop started
            logger.info("热键: 监听循环开始，监听 %d 键组合", len(self.vkeys))

            # 主循环：当运行状态为True时持续运行
            # Main loop: continue running when running state is True
            while self._running:
                # 检查所有配置的键是否同时按下（0x8000 最高位表示当前按下）
                # Check if all configured keys are pressed simultaneously (0x8000 high bit = currently pressed)
                all_pressed = True
                for vk in self.vkeys:
                    state = user32.GetAsyncKeyState(vk) & 0x8000
                    if not state:
                        all_pressed = False
                        break
                is_pressed = all_pressed

                # 检测从松开到按下的边沿触发（上升沿检测）
                # 当前按下且上一次未按下时触发
                # Detect edge trigger from release to press (rising edge detection)
                # Trigger when currently pressed and last time not pressed
                if is_pressed and not self._last_key_state:
                    # 先检查是否暂停，避免日志误导（暂停时不打"触发切换"）
                    # Check paused first to avoid misleading log (no "trigger" when paused)
                    if self._paused:
                        logger.info("热键: 检测到组合键但监听已暂停，忽略")
                    elif self.on_toggle:
                        # 记录检测到组合键按下日志
                        # Log detected combo pressed
                        logger.info("热键: 检测到组合键按下，触发切换")
                        # 在新线程中执行回调函数（避免阻塞监听循环）
                        # Execute callback function in new thread (avoid blocking listening loop)
                        threading.Thread(target=self.on_toggle, daemon=True).start()

                # 更新上一次按键状态为当前状态
                # Update last key state to current state
                self._last_key_state = is_pressed
                # 休眠20毫秒，降低CPU占用
                # Sleep 20 milliseconds, reduce CPU usage
                time.sleep(0.02)

            # 记录监听循环结束日志
            # Log listening loop ended
            logger.info("热键: 监听循环结束")
        except Exception as e:
            # 记录监听循环异常日志
            # Log listening loop exception
            logger.error("热键: 监听循环异常: %s", e)
