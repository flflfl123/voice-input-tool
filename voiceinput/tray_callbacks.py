# -*- coding: utf-8 -*-
# 托盘菜单回调处理模块 - 处理托盘右键菜单的各项操作
# 包括：添加热词、复制结果、清除LLM记忆
# Tray menu callback handler module - handle tray right-click menu operations
# Includes: add hotword, copy result, clear LLM history

# 导入日志记录库
# Import logging library
import logging

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


def add_hotword(text_processor):
    # 添加热词（通过简单输入框）
    # text_processor: 文本处理器实例
    # Add hotword (via simple input box)
    # text_processor: text processor instance

    # 使用tkinter简单输入框获取热词
    # Use tkinter simple input box to get hotword
    import tkinter as tk
    from tkinter import simpledialog
    # 创建临时Tk根窗口
    # Create temporary Tk root window
    root = tk.Tk()
    # 隐藏主窗口
    # Hide main window
    root.withdraw()
    # 弹出输入框获取热词
    # Pop up input box to get hotword
    word = simpledialog.askstring("添加热词", "请输入热词（格式：热词 = 替换词）：", parent=root)
    # 销毁临时窗口
    # Destroy temporary window
    root.destroy()
    # 检查是否输入了内容
    # Check if content was entered
    if word and word.strip():
        # 解析输入
        # Parse input
        parts = word.strip().split('=', 1)
        if len(parts) == 2:
            # 有等号，分别获取热词和替换词
            # Has equals sign, get hotword and replacement separately
            hot_word = parts[0].strip()
            replacement = parts[1].strip()
        else:
            # 没有等号，热词和替换词相同
            # No equals sign, hotword and replacement are the same
            hot_word = word.strip()
            replacement = word.strip()
        # 调用文本处理器添加热词
        # Call text processor to add hotword
        if text_processor:
            text_processor.add_hotword(hot_word, replacement)
            logger.info("托盘回调: 已添加热词 '%s' -> '%s'", hot_word, replacement)


def copy_result(text_processor):
    # 复制最近一次识别结果到剪贴板
    # text_processor: 文本处理器实例
    # Copy most recent recognition result to clipboard
    # text_processor: text processor instance

    # 获取最近一次识别结果
    # Get most recent recognition result
    result = ""
    if text_processor:
        result = text_processor.get_last_result()
    # 如果有结果，复制到剪贴板
    # If there's a result, copy to clipboard
    if result:
        try:
            # 使用tkinter复制到剪贴板
            # Use tkinter to copy to clipboard
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(result)
            root.update()
            root.destroy()
            logger.info("托盘回调: 已复制最近结果到剪贴板: %s", result[:50])
        except Exception as e:
            logger.warning("托盘回调: 复制结果失败: %s", e)


def clear_llm_history(text_processor):
    # 清除LLM对话记忆
    # text_processor: 文本处理器实例
    # Clear LLM conversation history
    # text_processor: text processor instance

    # 调用文本处理器清除LLM历史
    # Call text processor to clear LLM history
    if text_processor:
        text_processor.clear_llm_history()
        logger.info("托盘回调: 已清除LLM对话记忆")
