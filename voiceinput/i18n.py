# -*- coding: utf-8 -*-
# 国际化（i18n）模块 - 提供多语言翻译功能
# 从 locales/translations.json 加载翻译，提供翻译函数
# Internationalization (i18n) module - provides multi-language translation functions
# Loads translations from locales/translations.json, provides translation functions

# 导入JSON处理库
# Import JSON processing library
import json
# 导入日志记录库
# Import logging library
import logging
# 导入路径处理库
# Import path processing library
from pathlib import Path

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 翻译数据存储 ==========
# ========== Translation data storage ==========
# 存储所有翻译数据的字典（启动时只含英文，当前语言在 set_language() 时按需加载）
# Dictionary storing translation data (only English at startup, current lang loaded on-demand in set_language())
TRANSLATIONS = {}
# 原始完整翻译数据（按需加载用，启动时从 JSON 读取，之后按语言提取到 TRANSLATIONS）
# Raw complete translation data (for on-demand loading, read from JSON at startup, then extracted per lang to TRANSLATIONS)
_RAW_TRANSLATIONS = {}
# 当前界面语言，默认为英文
# Current interface language, default to English
CURRENT_LANG = "en"

# 支持的语言列表（按使用率排序）
SUPPORTED_LANGUAGES = [
    "zh_CN",  # 简体中文
    "zh_TW",  # 繁体中文
    "en",     # 英语
    "es",     # 西班牙语
    "ar",     # 阿拉伯语
    "hi",     # 印地语
    "id",     # 印尼语
    "ja",     # 日语
    "fr",     # 法语
    "de",     # 德语
    "ru",     # 俄语
    "pt",     # 葡萄牙语
    "it",     # 意大利语
    "tr",     # 土耳其语
    "pl",     # 波兰语
    "nl",     # 荷兰语
    "ko",     # 韩语
    "vi",     # 越南语
    "bn",     # 孟加拉语
    "ur",     # 乌尔都语
    "fil",    # 菲律宾语
    "ms",     # 马来语
    "th",     # 泰语
    "cs",     # 捷克语
    "hu",     # 匈牙利语
    "sv",     # 瑞典语
    "fi",     # 芬兰语
    "ro",     # 罗马尼亚语
    "uk",     # 乌克兰语
    "el",     # 希腊语
    "da",     # 丹麦语
    "no",     # 挪威语
    "he",     # 希伯来语
    "bg",     # 保加利亚语
    "hr",     # 克罗地亚语
]


def load_translations():
    # 加载翻译文件（按需加载优化：只加载当前语言 + 英文回退，不加载全部 35 种语言）
    # 159KB JSON 全量解析约 30-50ms，按需加载可节省大部分时间
    # 启动时只加载英文（回退语言），当前语言在 set_language() 时延迟加载
    # 返回True表示加载成功，False表示加载失败
    # Load translation file (on-demand: only load current lang + English fallback, not all 35 langs)
    # Full 159KB JSON parse takes ~30-50ms, on-demand loading saves most of it
    # Only load English (fallback) at startup, current lang lazy-loaded in set_language()
    # Return True if load successful, False if load failed

    # 获取翻译文件路径（当前文件的父目录的父目录下的locales目录）
    # Get translation file path (locales directory under parent's parent of current file)
    trans_file = Path(__file__).parent.parent / "locales" / "translations.json"
    # 记录开始加载翻译日志
    # Log start loading translations
    logger.info("i18n: 开始加载翻译文件 %s", trans_file)

    # 检查翻译文件是否存在
    # Check if translation file exists
    if trans_file.exists():
        try:
            # 以只读模式打开翻译文件，使用UTF-8编码
            # Open translation file in read-only mode with UTF-8 encoding
            with open(trans_file, "r", encoding="utf-8") as f:
                # 加载完整 JSON 数据到 _RAW_TRANSLATIONS（原始数据，供按需提取）
                # Load full JSON data to _RAW_TRANSLATIONS (raw data, for on-demand extraction)
                global _RAW_TRANSLATIONS, TRANSLATIONS
                _RAW_TRANSLATIONS = json.load(f)
            # 启动时只提取英文（回退语言）到 TRANSLATIONS，其他语言在 set_language() 时提取
            # At startup only extract English (fallback) to TRANSLATIONS, other langs extracted in set_language()
            TRANSLATIONS = {}
            for key, lang_dict in _RAW_TRANSLATIONS.items():
                # 跳过非字典类型（如 lang.fallback 列表）
                # Skip non-dict types (e.g. lang.fallback list)
                if isinstance(lang_dict, dict) and "en" in lang_dict:
                    TRANSLATIONS[key] = {"en": lang_dict["en"]}
                else:
                    # 非 dict 类型直接保留（如 lang.fallback）
                    # Non-dict types kept as-is (e.g. lang.fallback)
                    TRANSLATIONS[key] = lang_dict
            # 记录翻译加载成功日志
            # Log translation load success
            logger.info("i18n: 翻译文件加载成功（按需模式），共 %d 个翻译项", len(TRANSLATIONS))
            # 返回加载成功
            # Return load success
            return True
        except Exception as e:
            # 记录翻译加载失败日志
            # Log translation load failure
            logger.error("i18n: 翻译文件加载失败: %s", e)
            # 返回加载失败
            # Return load failure
            return False
    else:
        # 记录翻译文件不存在日志
        # Log translation file not found
        logger.error("i18n: 翻译文件不存在: %s", trans_file)
        # 返回加载失败
        # Return load failure
        return False


def _load_language(lang: str):
    # 按需加载指定语言的翻译到 TRANSLATIONS（启动时只加载英文，其他语言在此加载）
    # 提取 _RAW_TRANSLATIONS 中该语言的翻译，合并到 TRANSLATIONS 的每个键下
    # lang: 要加载的语言代码（如 "zh_CN"、"ja"）
    # Load specified language translations on-demand into TRANSLATIONS
    # Extract this language from _RAW_TRANSLATIONS, merge into each key in TRANSLATIONS
    # lang: language code to load (e.g. "zh_CN", "ja")
    global _RAW_TRANSLATIONS, TRANSLATIONS
    # 原始数据为空或语言已是英文（启动时已加载）则无需加载
    # Skip if raw data empty or language is English (already loaded at startup)
    if not _RAW_TRANSLATIONS or lang == "en":
        return
    # 遍历所有翻译键，提取目标语言并合并到 TRANSLATIONS
    # Iterate all translation keys, extract target lang and merge into TRANSLATIONS
    for key, lang_dict in _RAW_TRANSLATIONS.items():
        # 跳过非字典类型（如 lang.fallback 列表）
        # Skip non-dict types (e.g. lang.fallback list)
        if isinstance(lang_dict, dict) and lang in lang_dict:
            # 确保 TRANSLATIONS 中有该键（启动时只加载了英文，部分键可能没有）
            # Ensure TRANSLATIONS has this key (startup only loaded English, some keys may be missing)
            if key not in TRANSLATIONS:
                TRANSLATIONS[key] = {}
            # 合并目标语言翻译
            # Merge target language translation
            TRANSLATIONS[key][lang] = lang_dict[lang]
    logger.info("i18n: 已按需加载语言 '%s' 的翻译", lang)


def _(key: str) -> str:
    # 翻译函数：根据键名返回当前语言的文字
    # key: 翻译键名，例如 "app.title"
    # 返回对应语言的翻译文字，如果找不到则返回键名本身
    # Translation function: return text in current language based on key
    # key: translation key, e.g. "app.title"
    # Return translated text in corresponding language, return key itself if not found
    
    # 检查翻译键名是否存在
    # Check if translation key exists
    if key in TRANSLATIONS:
        # 获取该键名对应的所有语言翻译
        # Get all language translations for this key
        lang_dict = TRANSLATIONS[key]
        # 尝试获取当前语言的翻译
        # Try to get translation in current language
        if CURRENT_LANG in lang_dict:
            # 返回当前语言的翻译文字
            # Return translation in current language
            return lang_dict[CURRENT_LANG]
        # 如果当前语言不存在，尝试返回英文翻译
        # If current language doesn't exist, try to return English translation
        elif "en" in lang_dict:
            # 记录使用英文回退日志
            # Log using English fallback
            logger.debug("i18n: 键 '%s' 缺少 '%s' 翻译，使用英文回退", key, CURRENT_LANG)
            # 返回英文翻译
            # Return English translation
            return lang_dict["en"]
        # 如果英文也没有，返回第一个可用的翻译
        # If English also not available, return first available translation
        else:
            # 获取第一个可用的翻译值
            # Get first available translation value
            first_value = next(iter(lang_dict.values()), key)
            # 记录使用回退日志
            # Log using fallback
            logger.debug("i18n: 键 '%s' 缺少 '%s' 翻译，使用回退值", key, CURRENT_LANG)
            # 返回第一个可用的翻译
            # Return first available translation
            return first_value
    # 如果键名不存在，返回键名本身
    # If key doesn't exist, return key itself
    return key


def set_language(lang: str):
    # 设置当前界面语言
    # lang: 语言代码，例如 "en", "zh_CN", "fr"
    # 返回True表示设置成功，False表示语言不支持
    # Set current interface language
    # lang: language code, e.g. "en", "zh_CN", "fr"
    # Return True if set successful, False if language not supported
    
    # 检查语言是否在支持列表中
    # Check if language is in supported list
    if lang in SUPPORTED_LANGUAGES:
        # 设置全局当前语言
        # Set global current language
        global CURRENT_LANG
        CURRENT_LANG = lang
        # 按需加载该语言的翻译（启动时只加载了英文，其他语言在此加载到 TRANSLATIONS）
        # Load this language's translations on-demand (only English loaded at startup, others loaded here)
        _load_language(lang)
        # 记录语言切换日志
        # Log language switch
        logger.info("i18n: 语言已切换为: %s", lang)
        # 返回设置成功
        # Return set successful
        return True
    else:
        # 记录语言不支持日志
        # Log language not supported
        logger.error("i18n: 不支持的语言: %s", lang)
        # 返回设置失败
        # Return set failed
        return False


def get_current_language() -> str:
    # 获取当前界面语言
    # 返回当前语言代码
    # Get current interface language
    # Return current language code
    return CURRENT_LANG


def get_supported_languages() -> list:
    # 获取支持的语言列表
    # 返回支持的语言代码列表
    # Get list of supported languages
    # Return list of supported language codes
    return SUPPORTED_LANGUAGES.copy()


def get_language_name(lang_code: str) -> str:
    # 获取语言代码对应的显示名称
    # lang_code: 语言代码，例如 "en", "zh_CN"
    # 返回该语言在当前语言下的显示名称
    # Get display name for language code
    # lang_code: language code, e.g. "en", "zh_CN"
    # Return display name in current language
    
    # 构建语言名称的键名
    # Build key name for language name
    key = f"lang.{lang_code}"
    # 调用翻译函数获取语言名称
    # Call translation function to get language name
    return _(key)


def get_language_fallback_list(system_lang: str) -> list:
    # 根据系统语言获取按可能性排序的界面语言列表
    # 从 translations.json 的 lang.fallback 中读取回退列表
    # 回退列表中第一个是母语，后面3-5个是用户可能懂的语言
    # 将回退列表中的语言排在前面，其余支持语言排在后面
    # system_lang: 系统语言代码（如 "zh_CN", "en_US" 等）
    # 返回按可能性排序的界面语言代码列表（如 ["zh_CN", "en", "ja", "ko", ...]）
    # Get UI language list sorted by probability based on system language
    # Read fallback list from lang.fallback in translations.json
    # First in fallback list is native language, next 3-5 are likely understood
    # Put fallback languages first, then remaining supported languages
    # system_lang: system language code (e.g. "zh_CN", "en_US", etc.)
    # Return sorted list of UI language codes (e.g. ["zh_CN", "en", "ja", "ko", ...])
    
    # 如果翻译数据中没有 lang.fallback，返回默认排序的支持语言列表
    # If lang.fallback not in translation data, return default sorted supported list
    if "lang.fallback" not in TRANSLATIONS:
        logger.warning("i18n: translations.json 中没有 lang.fallback 数据")
        return SUPPORTED_LANGUAGES.copy()
    
    fallback_data = TRANSLATIONS["lang.fallback"]
    fallback_list = None
    
    # 尝试精确匹配（如 "zh_CN"）
    # Try exact match (e.g. "zh_CN")
    if system_lang in fallback_data:
        fallback_list = fallback_data[system_lang]
    
    # 尝试下划线格式匹配（如 "zh-cn" -> "zh_CN"）
    # Try underscore format match (e.g. "zh-cn" -> "zh_CN")
    if fallback_list is None:
        system_lang_normalized = system_lang.replace("-", "_")
        if system_lang_normalized in fallback_data:
            fallback_list = fallback_data[system_lang_normalized]
    
    # 尝试小写匹配
    # Try lowercase match
    if fallback_list is None:
        system_lang_lower = system_lang.lower()
        if system_lang_lower in fallback_data:
            fallback_list = fallback_data[system_lang_lower]
    
    # 尝试语言前缀匹配（如 "zh" -> ["zh_CN", "en", ...]）
    # Try language prefix match (e.g. "zh" -> ["zh_CN", "en", ...])
    if fallback_list is None:
        lang_prefix = system_lang.lower().split("_")[0].split("-")[0]
        for key, value in fallback_data.items():
            # 跳过注释键
            # Skip comment keys
            if key.startswith("#"):
                continue
            if key.lower().startswith(lang_prefix):
                fallback_list = value
                break
    
    # 如果没有找到回退列表，返回默认排序的支持语言列表
    # If no fallback list found, return default sorted supported list
    if fallback_list is None:
        logger.info("i18n: 未找到系统语言 %s 的回退列表", system_lang)
        return SUPPORTED_LANGUAGES.copy()
    
    # 按回退列表顺序排列支持的语言（可能性从大到小）
    # Sort supported languages by fallback list order (high to low probability)
    sorted_langs = []
    # 先添加回退列表中在支持列表里的语言（按回退顺序，即可能性从大到小）
    # First add languages from fallback list that are in supported list (in fallback order)
    for lang in fallback_list:
        if lang in SUPPORTED_LANGUAGES:
            sorted_langs.append(lang)
    
    # 再添加其余支持的语言（保持原始顺序）
    # Then add remaining supported languages (in original order)
    for lang in SUPPORTED_LANGUAGES:
        if lang not in sorted_langs:
            sorted_langs.append(lang)
    
    logger.info("i18n: 系统语言 %s，排序后的界面语言列表: %s", system_lang, sorted_langs)
    return sorted_langs


# 模块加载时自动加载翻译文件
# Automatically load translation file when module loads
load_translations()
