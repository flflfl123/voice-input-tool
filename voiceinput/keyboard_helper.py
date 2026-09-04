# -*- coding: utf-8 -*-
# 键盘模拟辅助模块 - 从main.py拆出
# 包含焦点恢复、粘贴模拟、按键模拟等功能
# 使用 AttachThreadInput 技巧绕过 SetForegroundWindow 限制
# Keyboard simulation helper module - split from main.py
# Contains focus restore, paste simulation, key simulation functions
# Uses AttachThreadInput trick to bypass SetForegroundWindow restriction

# 导入日志记录库
# Import logging library
import logging
# 导入时间库（用于焦点切换和按键模拟的延迟）
# Import time library (for delays in focus switching and key simulation)
import time

# 尝试导入 Windows API 库（用于模拟键盘和窗口焦点操作）
# Try importing Windows API libraries (for keyboard simulation and window focus)
# ponytail: 顶部统一导入，避免函数内重复import
try:
    import win32api
    import win32con
    import win32gui
    import win32process
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


def restore_focus(prev_window):
    # 恢复焦点到录音前的活动窗口
    # 使用 AttachThreadInput 技巧绕过 SetForegroundWindow 的限制
    # prev_window: 录音前记录的窗口句柄
    # 返回 True 表示成功恢复焦点，False 表示失败
    # Restore focus to the window that was active before recording
    # Use AttachThreadInput trick to bypass SetForegroundWindow restriction
    # prev_window: window handle recorded before recording
    # Return True if focus restored successfully, False otherwise

    # 检查pywin32是否可用
    # Check if pywin32 is available
    if not _HAS_WIN32:
        logger.warning("托盘: pywin32 未安装，无法恢复焦点")
        return False
    # 检查窗口句柄是否有效
    # Check if window handle is valid
    if not (prev_window and win32gui.IsWindow(prev_window)):
        logger.warning("托盘: 无有效的前台窗口句柄，无法恢复焦点")
        return False
    try:
        # 获取当前前台窗口和其线程ID
        # Get current foreground window and its thread ID
        cur_thread_id = win32api.GetCurrentThreadId()
        target_thread_id, _ = win32process.GetWindowThreadProcessId(prev_window)
        # 附加线程输入（让 SetForegroundWindow 可以成功）
        # Attach thread input (to make SetForegroundWindow succeed)
        attached = False
        if cur_thread_id != target_thread_id:
            win32process.AttachThreadInput(cur_thread_id, target_thread_id, True)
            attached = True
        try:
            # 显示窗口（如果最小化了）
            # Show window (if minimized)
            win32gui.ShowWindow(prev_window, win32con.SW_RESTORE)
            # 设置为前台窗口
            # Set as foreground window
            result = win32gui.SetForegroundWindow(prev_window)
            logger.info("托盘: 已恢复焦点到原窗口: %s (结果: %s)", prev_window, result)
        finally:
            # 确保无论上方是否异常，都分离线程输入（避免线程输入泄漏）
            # Ensure thread input is always detached (avoid thread input leak)
            if attached:
                try:
                    win32process.AttachThreadInput(cur_thread_id, target_thread_id, False)
                except Exception:
                    pass
        # 短暂延迟，确保窗口焦点切换完成
        # Brief delay to ensure window focus switch completes
        time.sleep(0.2)
        return True
    except Exception as e:
        # AttachThreadInput 失败时，尝试备用方案
        # When AttachThreadInput fails, try fallback
        logger.debug("托盘: AttachThreadInput 方式失败: %s，尝试备用方案", e)
        try:
            # 备用方案：发送 Alt 键释放锁，再设置前台窗口
            # Fallback: send Alt key to release lock, then set foreground
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(prev_window)
            logger.info("托盘: 备用方案恢复焦点到原窗口: %s", prev_window)
            time.sleep(0.2)
            return True
        except Exception as e2:
            logger.warning("托盘: 备用方案也失败: %s", e2)
            return False


def paste_to_cursor(prev_window):
    # 模拟 Ctrl+V 粘贴到光标位置
    # 需要先恢复焦点到录音前的活动窗口，再模拟粘贴
    # prev_window: 录音前记录的窗口句柄
    # Simulate Ctrl+V paste to cursor position
    # Need to restore focus first, then simulate paste
    # prev_window: window handle recorded before recording

    # 检查pywin32是否可用
    # Check if pywin32 is available
    if not _HAS_WIN32:
        logger.warning("托盘: pywin32 未安装，自动粘贴功能不可用")
        return
    try:
        # 恢复焦点到原窗口
        # Restore focus to original window
        if not restore_focus(prev_window):
            return
        # 短暂延迟，确保剪贴板内容已准备好
        # Brief delay to ensure clipboard content is ready
        time.sleep(0.1)
        # 记录即将模拟粘贴
        # Log about to simulate paste
        logger.info("托盘: 即将模拟 Ctrl+V 粘贴")
        # 模拟按下 Ctrl+V
        # Simulate pressing Ctrl+V
        win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
        win32api.keybd_event(ord('V'), 0, 0, 0)
        time.sleep(0.05)
        # 模拟释放 V 和 Ctrl
        # Simulate releasing V and Ctrl
        win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        logger.info("托盘: Ctrl+V 模拟完成")
    except Exception as e:
        logger.warning("托盘: 模拟粘贴失败: %s", e)


def simulate_key(prev_window, vk_code, name):
    # 模拟单个键盘按键的通用方法
    # prev_window: 录音前记录的窗口句柄
    # vk_code: 虚拟键码
    # name: 按键名称（用于日志）
    # Simulate a single keyboard key press (generic method)
    # prev_window: window handle recorded before recording
    # vk_code: virtual key code
    # name: key name (for logging)

    # 检查pywin32是否可用
    # Check if pywin32 is available
    if not _HAS_WIN32:
        logger.warning("口令: pywin32 未安装，%s操作不可用", name)
        return
    try:
        # 恢复焦点到原窗口
        # Restore focus to original window
        if not restore_focus(prev_window):
            logger.warning("口令: 恢复焦点失败，放弃%s", name)
            return
        # 模拟按键按下和释放
        # Simulate key press and release
        win32api.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        logger.info("口令: 已模拟%s", name)
    except Exception as e:
        logger.warning("口令: 模拟%s失败: %s", name, e)


def simulate_undo(prev_window):
    # 模拟 Ctrl+Z 撤销操作
    # prev_window: 录音前记录的窗口句柄
    # Simulate Ctrl+Z undo operation
    # prev_window: window handle recorded before recording
    simulate_key(prev_window, 0x5A, "撤销")  # VK_Z = 0x5A


def simulate_enter(prev_window):
    # 模拟 Enter 回车键
    # prev_window: 录音前记录的窗口句柄
    # Simulate Enter key
    # prev_window: window handle recorded before recording
    simulate_key(prev_window, 0x0D, "回车")  # VK_RETURN = 0x0D


def simulate_backspace(prev_window):
    # 模拟 Backspace 退格键
    # prev_window: 录音前记录的窗口句柄
    # Simulate Backspace key
    # prev_window: window handle recorded before recording
    simulate_key(prev_window, 0x08, "退格")  # VK_BACK = 0x08
