# -*- coding: utf-8 -*-
# 配置管理模块 - 加载和保存JSON配置文件
# 负责管理应用程序的所有配置项，包括ASR提供商、API密钥等
# Configuration management module - load and save JSON config files
# Manages all configuration items for the application, including ASR provider, API keys, etc.

# 导入JSON处理库
# Import JSON processing library
import json
# 导入日志记录库
# Import logging library
import logging
# 导入操作系统接口库
# Import operating system interface library
import os
# 导入路径处理库
# Import path processing library
from pathlib import Path

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 配置文件路径定义 ==========
# ========== Config file path definitions ==========
# 获取当前文件所在目录的父目录，拼接config目录
# Get parent directory of current file, append config directory
CONFIG_DIR = Path(__file__).parent.parent / "config"
# 构建完整的配置文件路径
# Build complete config file path
CONFIG_FILE = CONFIG_DIR / "config.json"
# 构建历史记录文件路径
# Build history file path
HISTORY_FILE = CONFIG_DIR / "history.json"

# ========== 默认配置项定义 ==========
# ========== Default configuration item definitions ==========
# 定义应用程序的默认配置字典
# Define default configuration dictionary for application
DEFAULT_CONFIG = {
    "asr_provider": "openai_compatible",  # ASR提供商类型（openai_compatible/doubao/volcengine）
                                          # ASR provider type (openai_compatible/doubao/volcengine)
    "app_key": "",                        # 豆包应用密钥
                                          # Doubao app key
    "access_key": "",                     # 火山引擎访问密钥
                                          # Volcano engine access key
    "resource_id": "volc.bigasr.sauc.duration",  # 豆包资源ID
                                                       # Doubao resource ID
    "cluster": "volcengine_streaming_common",    # 火山引擎集群名称
                                                 # Volcano engine cluster name
    "asr_mode": "bigmodel_async",         # ASR识别模式
                                          # ASR recognition mode
    "base_url": "",                       # OpenAI兼容API基础地址
                                          # OpenAI compatible API base URL
    "api_key": "",                        # OpenAI兼容API密钥
                                          # OpenAI compatible API key
    "model": "whisper-1",                 # 模型名称
                                          # Model name
    "sample_rate": 16000,                 # 音频采样率（Hz）
                                          # Audio sample rate (Hz)
    "chunk_size": 3200,                   # 音频块大小（字节）
                                          # Audio chunk size (bytes)
    "autostart": False,                   # 开机自启动（默认关闭）
                                          # Auto-start on boot (default off)
    "theme": "dark",                      # 主题模式（默认暗色）
                                          # Theme mode (default dark)
    "floating_enabled": True,             # 悬浮窗功能（默认开启）
                                          # Floating window feature (default on)
    "language": "en",                     # 界面语言（默认英文）
                                          # Interface language (default English)
    "font_scale": 1.0,                    # 字体缩放系数（0.8-1.5，默认 1.0 不缩放，只影响字体不影响控件）
                                          # Font scale factor (0.8-1.5, default 1.0, only affects fonts not widgets)

    # ========== 文本后处理配置 ==========
    # ========== Text post-processing configuration ==========
    "remove_trailing_punct": True,        # 去除末尾逗句号（默认开启）
                                          # Remove trailing punctuation (default on)
    "itn_enabled": True,                  # ITN数字转换（默认开启）
                                          # ITN number conversion (default on)
    "hot_enabled": True,                  # 热词替换（默认开启）
                                          # Hotword replacement (default on)
    "hot_threshold": 0.85,                # 热词精确匹配阈值（0.0~1.0）
                                          # Hotword exact match threshold (0.0~1.0)
    "hot_rule_enabled": True,             # 正则规则替换（默认开启）
                                          # Regex rule replacement (default on)
    "llm_enabled": False,                 # LLM角色处理（默认关闭）
                                          # LLM role processing (default off)
    "llm_base_url": "",                   # LLM API基础地址（为空时使用ASR的base_url）
                                          # LLM API base URL (use ASR base_url if empty)
    "llm_api_key": "",                    # LLM API密钥（为空时使用ASR的api_key）
                                          # LLM API key (use ASR api_key if empty)
    "llm_model": "gpt-3.5-turbo",        # LLM模型名称
                                          # LLM model name
    "diary_enabled": True,                # 日记归档（默认开启）
                                          # Diary archive (default on)
}


def detect_system_language() -> str:
    # 检测 Windows 系统语言并返回匹配的界面语言
    # 从 i18n 模块读取 translations.json 中的 lang.fallback 数据
    # 返回界面语言代码（如 "zh_CN", "en" 等）
    # Detect Windows system language and return matched UI language
    # Read lang.fallback data from translations.json via i18n module
    # Return UI language code (e.g. "zh_CN", "en", etc.)
    
    try:
        # 导入 locale 模块获取系统语言
        # Import locale module to get system language
        import locale
        # 获取系统默认语言（格式如 "zh_CN", "en_US" 等）
        # Get system default language (format like "zh_CN", "en_US", etc.)
        system_lang = locale.getdefaultlocale()[0]
        
        if system_lang is None:
            # 如果获取失败，返回默认英文
            # If detection fails, return default English
            logger.info("配置: 无法检测系统语言，使用默认英文")
            return "en"
        
        # 从 i18n 模块获取按可能性排序的界面语言列表
        # Get sorted UI language list from i18n module
        from voiceinput.i18n import get_language_fallback_list
        sorted_langs = get_language_fallback_list(system_lang)
        # 取排序后的第一个语言（可能性最高，即用户母语）
        # Take the first language in sorted list (highest probability, user's native language)
        matched_lang = sorted_langs[0] if sorted_langs else "en"
        logger.info("配置: 检测到系统语言 %s，匹配到界面语言: %s", system_lang, matched_lang)
        return matched_lang
        
    except Exception as e:
        # 捕获异常，返回默认英文
        # Catch exception, return default English
        logger.warning("配置: 检测系统语言失败: %s，使用默认英文", e)
        return "en"


def load_config() -> dict:
    # 加载配置文件
    # 从config.json读取配置，如果文件不存在则使用默认配置
    # 返回配置字典
    # Load configuration file
    # Read config from config.json, use default config if file doesn't exist
    # Return config dictionary
    
    # 记录开始加载配置日志
    # Log start loading config
    logger.info("配置: 开始加载配置文件")
    # 复制默认配置字典
    # Copy default config dictionary
    config = dict(DEFAULT_CONFIG)

    # 检查配置文件是否存在
    # Check if config file exists
    if CONFIG_FILE.exists():
        # 记录找到配置文件日志
        # Log found config file
        logger.info("配置: 找到配置文件 %s", CONFIG_FILE)
        try:
            # 以只读模式打开配置文件，使用UTF-8编码
            # Open config file in read-only mode with UTF-8 encoding
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                # 从文件加载JSON数据
                # Load JSON data from file
                saved = json.load(f)
                # 配置迁移：旧字段 ui_scale 改名为 font_scale
                # 若旧配置有 ui_scale 但无 font_scale，迁移值
                # Config migration: old field ui_scale renamed to font_scale
                # If old config has ui_scale but no font_scale, migrate the value
                if "ui_scale" in saved and "font_scale" not in saved:
                    saved["font_scale"] = saved.pop("ui_scale")
                    logger.info("配置: 迁移旧字段 ui_scale -> font_scale")
                # 将保存的配置更新到默认配置中
                # Update saved config into default config
                config.update(saved)
            # 记录配置加载成功日志
            # Log config load success
            logger.info("配置: 配置文件加载成功，已应用 %d 个配置项", len(saved))
            # 记录当前ASR提供商日志
            # Log current ASR provider
            logger.info("配置: 当前 ASR 提供商: %s", config.get("asr_provider", "未知"))
        except Exception as e:
            # 记录加载配置文件失败日志
            # Log config file load failure
            logger.error("配置: 加载配置文件失败: %s", e)
    else:
        # 记录未找到配置文件日志
        # Log config file not found
        logger.info("配置: 未找到配置文件，使用默认配置")
        # 首次启动：自动检测系统语言并设置界面语言
        # First launch: auto-detect system language and set UI language
        detected_lang = detect_system_language()
        config["language"] = detected_lang
        logger.info("配置: 首次启动，自动设置界面语言为: %s", detected_lang)

    # 返回最终配置字典
    # Return final config dictionary
    return config


def save_config(config: dict):
    # 保存配置到文件（原子写入：先写临时文件，再原子重命名，防止崩溃导致配置丢失）
    # 原子写入流程：写 .tmp 临时文件 → flush+fsync 确保落盘 → os.replace 原子替换
    # 这样即使写入过程中断电/崩溃，原配置文件仍然完整
    # config: 要保存的配置字典
    # Save config to file (atomic write: write temp file first, then atomic rename)
    # Atomic flow: write .tmp -> flush+fsync -> os.replace atomic swap
    # Original config stays intact even if crash during write
    # config: config dictionary to save

    # 记录开始保存配置日志
    # Log start saving config
    logger.info("配置: 开始保存配置到 %s", CONFIG_FILE)
    # 临时文件路径（与目标文件同目录，确保 os.replace 是原子操作）
    # Temp file path (same directory as target, ensures os.replace is atomic)
    tmp_file = str(CONFIG_FILE) + ".tmp"
    try:
        # 确保配置目录存在，如果不存在则创建（包括父目录）
        # Ensure config directory exists, create if not (including parent directories)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # 记录配置目录已确保存在日志
        # Log config directory ensured
        logger.info("配置: 配置目录已确保存在")
        # 先写入临时文件（避免直接截断原文件，写入失败时原文件不受影响）
        # Write to temp file first (avoid truncating original, original safe on failure)
        with open(tmp_file, "w", encoding="utf-8") as f:
            # 将配置字典写入临时文件，不转义ASCII字符，缩进2个空格
            # Write config dictionary to temp file, don't escape ASCII, indent 2 spaces
            json.dump(config, f, ensure_ascii=False, indent=2)
            # 刷新缓冲区并强制写入磁盘（确保数据落盘后再重命名）
            # Flush buffer and force write to disk (ensure data persisted before rename)
            f.flush()
            os.fsync(f.fileno())
        # 原子替换：os.replace 在 Windows/Linux 上都是原子操作
        # Atomic replace: os.replace is atomic on both Windows and Linux
        os.replace(tmp_file, CONFIG_FILE)
        # 记录配置已成功保存日志
        # Log config successfully saved
        logger.info("配置: 配置已成功保存")
    except Exception as e:
        # 记录保存配置失败日志
        # Log save config failure
        logger.error("配置: 保存配置失败: %s", e)
        # 清理可能残留的临时文件
        # Clean up residual temp file if exists
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except Exception:
            pass


def load_history() -> list:
    # 加载历史记录
    # 从history.json读取历史记录，如果文件不存在则返回空列表
    # 返回历史记录列表
    
    # 记录开始加载历史记录日志
    logger.info("配置: 开始加载历史记录文件")
    
    # 检查历史记录文件是否存在
    if HISTORY_FILE.exists():
        # 记录找到历史记录文件日志
        logger.info("配置: 找到历史记录文件 %s", HISTORY_FILE)
        try:
            # 以只读模式打开历史记录文件，使用UTF-8编码
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                # 从文件加载JSON数据
                history = json.load(f)
            # 记录历史记录加载成功日志
            logger.info("配置: 历史记录加载成功，共 %d 条记录", len(history))
            # 返回历史记录列表
            return history
        except Exception as e:
            # 记录加载历史记录失败日志
            logger.error("配置: 加载历史记录失败: %s", e)
            # 返回空列表
            return []
    else:
        # 记录未找到历史记录文件日志
        logger.info("配置: 未找到历史记录文件，使用空列表")
        # 返回空列表
        return []


def save_history(history: list):
    # 保存历史记录到文件（原子写入：先写临时文件，再原子重命名，防止崩溃导致历史丢失）
    # history: 要保存的历史记录列表
    # Save history to file (atomic write: temp file + atomic rename, prevent history loss on crash)

    # 记录开始保存历史记录日志
    logger.info("配置: 开始保存历史记录到 %s", HISTORY_FILE)
    # 临时文件路径（与目标文件同目录，确保 os.replace 是原子操作）
    # Temp file path (same directory, ensures os.replace atomic)
    tmp_file = str(HISTORY_FILE) + ".tmp"
    try:
        # 确保配置目录存在，如果不存在则创建（包括父目录）
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # 记录配置目录已确保存在日志
        logger.info("配置: 配置目录已确保存在")
        # 先写入临时文件（避免直接截断原文件）
        # Write to temp file first (avoid truncating original)
        with open(tmp_file, "w", encoding="utf-8") as f:
            # 将历史记录列表写入临时文件，不转义ASCII字符，缩进2个空格
            json.dump(history, f, ensure_ascii=False, indent=2)
            # 刷新缓冲区并强制写入磁盘
            # Flush buffer and force write to disk
            f.flush()
            os.fsync(f.fileno())
        # 原子替换
        # Atomic replace
        os.replace(tmp_file, HISTORY_FILE)
        # 记录历史记录已成功保存日志
        logger.info("配置: 历史记录已成功保存，共 %d 条记录", len(history))
    except Exception as e:
        # 记录保存历史记录失败日志
        logger.error("配置: 保存历史记录失败: %s", e)
        # 清理可能残留的临时文件
        # Clean up residual temp file if exists
        try:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)
        except Exception:
            pass


def clear_history():
    # 清空历史记录文件
    # 删除history.json文件
    
    # 记录开始清空历史记录日志
    logger.info("配置: 开始清空历史记录文件")
    try:
        # 检查历史记录文件是否存在
        if HISTORY_FILE.exists():
            # 删除历史记录文件
            HISTORY_FILE.unlink()
            # 记录历史记录文件已删除日志
            logger.info("配置: 历史记录文件已删除")
        else:
            # 记录历史记录文件不存在日志
            logger.info("配置: 历史记录文件不存在，无需清空")
    except Exception as e:
        # 记录清空历史记录失败日志
        logger.error("配置: 清空历史记录失败: %s", e)
