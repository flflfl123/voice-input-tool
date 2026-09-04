# -*- coding: utf-8 -*-
# 日记归档模块 - 按日期保存每一句语音及其识别结果
# 保存到 diary/ 目录，按 年/月/日.md 格式组织
# 参考自 CapsWriter-Offline 项目 (https://github.com/HaujetZhao/CapsWriter-Offline)
# CapsWriter-Offline 采用 MIT 协议开源，作者：HaujetZhao
# Diary archive module - save each voice input and recognition result by date
# Save to diary/ directory, organized by year/month/day.md format
# Referenced from CapsWriter-Offline project's diary_writer.py

# 导入日志记录库
# Import logging library
import logging
# 导入时间处理库
# Import time processing library
import time
# 导入路径处理库
# Import path processing library
from pathlib import Path

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 日记目录路径 ==========
# ========== Diary directory path ==========
# 日记保存在项目根目录的 diary/ 目录下
# Diary is saved in diary/ directory under project root
DIARY_DIR = Path(__file__).parent.parent / "diary"


class DiaryWriter:
    # 日记写入器类
    # 按日期将语音识别结果写入Markdown文件
    # Diary writer class
    # Write speech recognition results to Markdown file by date

    def __init__(self, diary_dir: str = None):
        # 初始化日记写入器
        # diary_dir: 日记保存目录，默认为项目根目录的 diary/ 目录
        # Initialize diary writer
        # diary_dir: diary save directory, default to diary/ under project root

        # 保存日记目录路径
        # Save diary directory path
        self._diary_dir = Path(diary_dir) if diary_dir else DIARY_DIR
        # 确保日记目录存在
        # Ensure diary directory exists
        self._diary_dir.mkdir(parents=True, exist_ok=True)
        # 记录初始化日志
        # Log initialization
        logger.info("日记: 初始化完成，日记目录: %s", self._diary_dir)

    def write(self, text: str, timestamp: float = None):
        # 写入一条日记记录
        # text: 识别文本
        # timestamp: 时间戳（秒），默认为当前时间
        # Write a diary record
        # text: recognition text
        # timestamp: timestamp (seconds), default to current time

        # 如果文本为空，跳过
        # If text is empty, skip
        if not text or not text.strip():
            return

        # 如果没有提供时间戳，使用当前时间
        # If no timestamp provided, use current time
        if timestamp is None:
            timestamp = time.time()

        try:
            # 将时间戳转换为本地时间
            # Convert timestamp to local time
            local_time = time.localtime(timestamp)
            # 提取年、月、日、时分秒
            # Extract year, month, day, hour:minute:second
            year = time.strftime('%Y', local_time)
            month = time.strftime('%m', local_time)
            day = time.strftime('%d', local_time)
            hms = time.strftime('%H:%M:%S', local_time)

            # 构建日记目录路径：diary/年/月/
            # Build diary directory path: diary/year/month/
            folder = self._diary_dir / year / month
            # 确保目录存在
            # Ensure directory exists
            folder.mkdir(parents=True, exist_ok=True)

            # 构建日记文件路径：diary/年/月/日.md
            # Build diary file path: diary/year/month/day.md
            file_path = folder / f"{day}.md"

            # 如果文件不存在，创建并写入文件头
            # If file doesn't exist, create and write header
            if not file_path.exists():
                self._create_diary_file(file_path, year, month, day)

            # 以追加模式打开日记文件
            # Open diary file in append mode
            with open(file_path, "a", encoding="utf-8") as f:
                # 写入时间和识别文本（使用二级标题格式，与CapsWriter-Offline一致）
                # Write time and recognition text (using h2 heading format, consistent with CapsWriter-Offline)
                f.write(f"## {hms}\n\n{text.strip()}\n\n")

            # 记录写入成功日志
            # Log write success
            logger.info("日记: 已写入日记 %s/%s/%s.md: %s", year, month, day, text[:30])

        except Exception as e:
            # 记录写入失败日志
            # Log write failure
            logger.error("日记: 写入日记失败: %s", e)

    def _create_diary_file(self, file_path: Path, year: str, month: str, day: str):
        # 创建新的日记文件并写入文件头
        # file_path: 日记文件路径
        # year: 年份字符串
        # month: 月份字符串
        # day: 日期字符串
        # Create new diary file and write header
        # file_path: diary file path
        # year: year string
        # month: month string
        # day: day string

        try:
            # 以写入模式创建文件
            # Create file in write mode
            with open(file_path, "w", encoding="utf-8") as f:
                # 写入Markdown标题（与CapsWriter-Offline格式一致）
                # Write Markdown title (consistent with CapsWriter-Offline format)
                f.write(f"# {year}年{month}月{day}日\n\n")
            # 记录创建成功日志
            # Log creation success
            logger.info("日记: 已创建日记文件 %s", file_path)
        except Exception as e:
            # 记录创建失败日志
            # Log creation failure
            logger.error("日记: 创建日记文件失败: %s", e)
