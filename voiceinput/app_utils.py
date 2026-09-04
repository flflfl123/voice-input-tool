# -*- coding: utf-8 -*-
# 应用程序辅助工具模块 - 从main.py拆出
# 包含日志设置、DPI感知、单实例锁、图标生成等功能
# Application utility module - split from main.py
# Contains logging setup, DPI awareness, single instance lock, icon generation

# 导入日志记录库
# Import logging library
import logging
# 导入操作系统接口库
# Import operating system interface library
import os
# 导入Microsoft C运行时库（用于文件锁定）
# Import Microsoft C runtime library (for file locking)
import msvcrt
# 导入Windows系统API调用库
# Import Windows system API library
import ctypes
# 导入路径处理库
# Import path processing library
from pathlib import Path

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 日志文件路径 ==========
# ========== Log file path ==========
# 日志文件保存在 config 目录下
# Log file is saved in config directory
LOG_DIR = Path(__file__).parent.parent / "config"
LOG_FILE = LOG_DIR / "app.log"

# ========== 单实例锁文件句柄 ==========
# ========== Single instance lock file handle ==========
# 全局变量，用于保存锁文件句柄，防止程序重复启动
# Global variable to store lock file handle, prevent duplicate program launch
_lock_file = None


def setup_file_logging():
    # 设置日志文件处理器（性能优化：磁盘 IO 放后台线程，避免阻塞启动）
    # 使用按天轮转（TimedRotatingFileHandler），每天午夜创建新文件，保留 7 天备份
    # 超过 7 天的日志自动删除，避免磁盘占用无限增长
    # 启动时只创建目录（快），文件处理器创建和轮转检查放后台线程
    # 返回日志处理器对象（可能为 None，如果后台线程尚未完成）
    # Setup log file handler (performance: disk IO in background thread to avoid blocking startup)
    # Uses daily rotation (TimedRotatingFileHandler), creates new file at midnight, keeps 7 day backups
    # Logs older than 7 days are auto-deleted to avoid unbounded disk usage
    # Only create directory at startup (fast), file handler creation and rotation check in background
    # Returns log handler object (may be None if background thread not yet finished)

    # 确保日志目录存在（同步，快速操作）
    # Ensure log directory exists (synchronous, fast)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 后台线程中创建文件处理器并添加到日志记录器
    # Create file handler and add to logger in background thread
    def _setup_in_thread():
        # 导入按时间轮转的日志处理器
        # Import timed rotating file handler
        from logging.handlers import TimedRotatingFileHandler
        # 创建按天轮转的文件处理器
        # when='midnight'：每天午夜轮转
        # backupCount=7：保留 7 天的备份文件，超过 7 天的自动删除
        # encoding='utf-8'：使用 UTF-8 编码
        # Create timed rotating file handler
        # when='midnight': rotate at midnight daily
        # backupCount=7: keep 7 day backups, auto-delete older
        # encoding='utf-8': use UTF-8 encoding
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when='midnight',       # 每天午夜轮转 / Rotate at midnight
            interval=1,            # 间隔 1 天 / Interval of 1 day
            backupCount=7,         # 保留 7 天备份 / Keep 7 day backups
            encoding='utf-8'
        )
        # 设置日志格式：时间 - 级别 - 消息
        # Set log format: time - level - message
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        # 设置日志级别为INFO（记录所有信息）
        # Set log level to INFO (record all information)
        file_handler.setLevel(logging.INFO)
        # 将处理器添加到VoiceInput日志记录器
        # Add handler to VoiceInput logger
        logging.getLogger("VoiceInput").addHandler(file_handler)

    # 启动守护线程执行日志初始化（不阻塞主线程启动）
    # Start daemon thread to execute log init (non-blocking main thread startup)
    import threading
    threading.Thread(target=_setup_in_thread, daemon=True).start()

    return None


def enable_dpi_awareness():
    # 启用 Windows DPI 感知
    # 使程序在高 DPI 屏幕上正确显示，避免界面模糊
    # 优先使用Per-Monitor DPI Aware（每个显示器独立DPI）
    # Enable Windows DPI awareness
    # Make program display correctly on high DPI screens, avoid blurry interface
    # Prefer Per-Monitor DPI Aware (independent DPI for each monitor)

    try:
        # 尝试设置Per-Monitor DPI Aware（级别2）
        # 这允许程序在多显示器环境下每个显示器使用不同的DPI缩放
        # Try to set Per-Monitor DPI Aware (level 2)
        # This allows program to use different DPI scaling per monitor in multi-monitor environment
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as e:
        # 如果Per-Monitor DPI Aware失败，尝试降级方案
        # If Per-Monitor DPI Aware fails, try fallback
        logger.debug("DPI: Per-Monitor感知设置失败: %s", e)
        try:
            # 尝试设置System DPI Aware（系统级DPI）
            # 这是较低级别的DPI感知，但至少能避免界面模糊
            # Try to set System DPI Aware (system-level DPI)
            # This is lower level DPI awareness, but at least avoids blurry interface
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e2:
            # 如果两种方式都失败，记录日志（不影响程序运行）
            # If both methods fail, log it (doesn't affect program operation)
            logger.debug("DPI: System感知也失败: %s", e2)


def acquire_single_instance_lock():
    # 获取单实例锁
    # 防止程序重复启动，确保只有一个实例在运行
    # 返回True表示成功获取锁，False表示已有实例在运行
    # Acquire single instance lock
    # Prevent duplicate program launch, ensure only one instance is running
    # Return True if lock acquired successfully, False if instance already running

    # 声明使用全局锁文件句柄变量
    # Declare use of global lock file handle variable
    global _lock_file
    # 构建锁文件路径（在系统临时目录下）
    # Build lock file path (in system temp directory)
    lock_path = Path(os.environ.get("TEMP", ".")) / "voice_input.lock"
    try:
        # 打开锁文件（如果不存在则创建）
        # Open lock file (create if not exists)
        _lock_file = open(lock_path, "w")
        # 尝试获取非阻塞文件锁（LK_NBLCK表示非阻塞）
        # 锁定1个字节
        # Try to acquire non-blocking file lock (LK_NBLCK means non-blocking)
        # Lock 1 byte
        msvcrt.locking(_lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        # 成功获取锁，返回True
        # Lock acquired successfully, return True
        return True
    except (IOError, OSError):
        # 如果获取锁失败（文件已被锁定）
        # 说明已有实例在运行
        # If lock acquisition failed (file already locked)
        # This means another instance is already running
        if _lock_file:
            # 关闭锁文件
            # Close lock file
            try:
                _lock_file.close()
            except Exception as e:
                logger.debug("单实例: 锁文件关闭异常: %s", e)
            # 清空锁文件句柄
            # Clear lock file handle
            _lock_file = None
        # 返回False表示获取锁失败
        # Return False indicating lock acquisition failed
        return False


def release_single_instance_lock():
    # 释放单实例锁文件
    # 在程序退出时调用，关闭锁文件句柄
    # Release single instance lock file
    # Called when program exits, close lock file handle

    # 声明使用全局锁文件句柄变量
    # Declare use of global lock file handle variable
    global _lock_file
    # 检查锁文件是否存在
    # Check if lock file exists
    if _lock_file:
        try:
            # 关闭锁文件
            # Close lock file
            _lock_file.close()
        except Exception as e:
            logger.debug("退出: 锁文件关闭异常: %s", e)
        # 清空锁文件句柄
        # Clear lock file handle
        _lock_file = None


def load_icon(recording: bool = False):
    # 加载托盘图标
    # 根据录音状态显示不同颜色的图标
    # recording: 是否正在录音
    # 返回PIL Image对象，如果PIL未安装则返回None
    # Load tray icon
    # Display different color icons based on recording state
    # recording: whether currently recording
    # Return PIL Image object, or None if PIL not installed

    try:
        # 导入PIL图像处理库
        # Import PIL image processing library
        from PIL import Image, ImageDraw

        # 设置图标尺寸为128x128像素
        # Set icon size to 128x128 pixels
        size = 128
        # 创建透明背景的RGBA图像
        # Create RGBA image with transparent background
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        # 创建绘图对象
        # Create drawing object
        draw = ImageDraw.Draw(img)

        # 判断是否正在录音
        # Check if recording
        if recording:
            # 录音中：绘制红色圆形图标
            # Recording: draw red circular icon
            # 绘制外圆（深红色填充，更深红色边框，边框宽度4像素）
            # Draw outer circle (dark red fill, darker red border, 4px border width)
            draw.ellipse([16, 16, 112, 112], fill=(220, 50, 50), outline=(180, 30, 30), width=4)
            # 绘制内圆（亮红色填充）
            # Draw inner circle (bright red fill)
            draw.ellipse([40, 40, 88, 88], fill=(255, 80, 80))
        else:
            # 就绪状态：绘制灰色圆形图标
            # Ready state: draw gray circular icon
            # 绘制外圆（深灰色填充，更深灰色边框，边框宽度4像素）
            # Draw outer circle (dark gray fill, darker gray border, 4px border width)
            draw.ellipse([16, 16, 112, 112], fill=(60, 60, 60), outline=(40, 40, 40), width=4)
            # 绘制内圆（中灰色填充）
            # Draw inner circle (medium gray fill)
            draw.ellipse([40, 40, 88, 88], fill=(100, 100, 100))

        # 返回绘制好的图标图像
        # Return drawn icon image
        return img
    except ImportError:
        # 如果PIL库未安装，返回None
        # If PIL library not installed, return None
        return None


def create_default_icon():
    # 创建默认托盘图标
    # 当load_icon失败时使用的备用图标
    # 返回PIL Image对象，如果PIL未安装则返回None
    # Create default tray icon
    # Fallback icon used when load_icon fails
    # Return PIL Image object, or None if PIL not installed

    try:
        # 导入PIL图像处理库
        # Import PIL image processing library
        from PIL import Image
        # 创建128x128像素的灰色RGBA图像（不透明）
        # Create 128x128 pixel gray RGBA image (opaque)
        return Image.new("RGBA", (128, 128), (80, 80, 80, 255))
    except ImportError:
        # 如果PIL库未安装，返回None
        # If PIL library not installed, return None
        return None
