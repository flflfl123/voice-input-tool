# -*- coding: utf-8 -*-
# 数字ITN逆文本规范化模块 - 将中文数字转为阿拉伯数字
# 例如：「十五六个」→「15~16个」，「三百五十」→「350」
# 参考自 CapsWriter-Offline 项目 (https://github.com/HaujetZhao/CapsWriter-Offline)
# CapsWriter-Offline 采用 MIT 协议开源，作者：HaujetZhao
# ITN (Inverse Text Normalization) module - convert Chinese numbers to Arabic
# e.g. "十五六个" -> "15~16个", "三百五十" -> "350"
# Referenced from CapsWriter-Offline project's chinese_itn.py

# 导入正则表达式库
# Import regular expression library
import re
# 导入日志记录库
# Import logging library
import logging

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# 保护词列表：这些词中的"一"是副词/语气词，不是数字，不应转换
# cn2an 库有词典能正确处理，此列表仅用于内置回退方案
# Protected words: "一" in these words is adverb/particle, not a number
# cn2an handles this correctly via dictionary, this list is for built-in fallback only
_PROTECTED_WORDS = [
    "一会儿", "一样", "一直", "一起", "一些", "一定", "一般", "一点",
    "一边", "一面", "一时", "一生", "一切", "一共", "一向", "一再",
    "一旦", "一齐", "一同", "一并", "一连", "一瞬", "一瞥", "一晃",
    "一声", "一步步", "一步一步",
]

# cn2an 未安装时只警告一次的标志
# Flag to warn only once when cn2an is not installed
_cn2an_warned = False


def chinese_to_num(text: str) -> str:
    # 将文本中的中文数字转换为阿拉伯数字
    # 处理流程：先尝试cn2an库转换基础数字，再应用增强规则处理特殊场景
    # text: 输入文本
    # 返回转换后的文本
    # Convert Chinese numbers in text to Arabic numbers
    # Process: first try cn2an for basic numbers, then apply enhanced rules for special cases
    # text: input text
    # Return converted text

    # 如果文本为空，直接返回
    # If text is empty, return directly
    if not text:
        return text

    # 保存原始文本用于比较
    # Save original text for comparison
    original = text

    # ========== 第一步：应用增强ITN规则 ==========
    # 处理cn2an无法覆盖的场景：百分比、分数、范围/约数、日期
    # Step 1: Apply enhanced ITN rules
    # Handle scenarios cn2an cannot cover: percentage, fraction, range/approx, date
    from .itn_rules import apply_enhanced_rules
    text = apply_enhanced_rules(text)

    # ========== 第二步：cn2an基础数字转换 ==========
    # Step 2: cn2an basic number conversion
    try:
        # 尝试使用 cn2an 库进行转换（更准确）
        # Try using cn2an library for conversion (more accurate)
        import cn2an
        # 使用 cn2an 的 transform 函数，自动识别并转换文本中的中文数字
        # Use cn2an's transform function to auto-detect and convert Chinese numbers
        result = cn2an.transform(text, "cn2an")
        # 返回转换结果
        # Return conversion result
        if result != original:
            logger.info("ITN: 数字转换 '%s' -> '%s'", original, result)
        return result
    except ImportError:
        # cn2an 库未安装，使用内置简单转换（只提示一次，避免每次调用都打印）
        # cn2an library not installed, use built-in simple conversion (log once only)
        global _cn2an_warned
        if not _cn2an_warned:
            logger.info("ITN: cn2an 库未安装，使用内置简单数字转换")
            _cn2an_warned = True
        result = _simple_chinese_to_num(text)
        if result != original:
            logger.info("ITN: 数字转换 '%s' -> '%s'", original, result)
        return result
    except Exception as e:
        # 转换失败时记录警告，返回原文
        # Log warning on conversion failure, return original text
        logger.warning("ITN: 数字转换失败: %s，返回原文", e)
        return text


def _simple_chinese_to_num(text: str) -> str:
    # 内置简单中文数字转换（cn2an未安装时的回退方案）
    # 仅处理常见的整数和小数
    # text: 输入文本
    # 返回转换后的文本
    # Built-in simple Chinese number conversion (fallback when cn2an not installed)
    # Only handles common integers and decimals
    # text: input text
    # Return converted text

    # 第一步：用占位符保护"一"字开头的副词/语气词，避免误转
    # Step 1: Protect "一"-prefixed adverbs/particles with placeholders to avoid false conversion
    placeholders = {}
    for i, word in enumerate(_PROTECTED_WORDS):
        # 用不可见字符做占位符，避免与正常文本冲突
        # Use invisible characters as placeholders to avoid collision with normal text
        ph = f"\x00P{i}\x00"
        placeholders[ph] = word
        text = text.replace(word, ph)

    # 中文数字字符到阿拉伯数字的映射
    # Mapping from Chinese number characters to Arabic numbers
    cn_digits = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '两': 2,
    }
    # 中文单位到倍数的映射
    # Mapping from Chinese unit characters to multipliers
    cn_units = {
        '十': 10, '百': 100, '千': 1000, '万': 10000,
        '亿': 100000000,
    }

    # 构建匹配中文数字的正则模式
    # Build regex pattern to match Chinese numbers
    # 匹配连续的中文数字字符（包含单位和数字）
    # Match consecutive Chinese number characters (including units and digits)
    pattern = r'[零一二三四五六七八九十百千万亿两]+'

    def _convert_match(match):
        # 转换单个匹配到的中文数字字符串
        # Convert a single matched Chinese number string
        cn_str = match.group()
        # 调用转换函数
        # Call conversion function
        result = _convert_cn_number(cn_str, cn_digits, cn_units)
        # 如果转换成功返回数字字符串，否则返回原文
        # If conversion successful return number string, otherwise return original
        return str(result) if result is not None else cn_str

    # 使用正则替换所有匹配的中文数字
    # Use regex to replace all matched Chinese numbers
    result = re.sub(pattern, _convert_match, text)

    # 第二步：还原占位符为原始保护词
    # Step 2: Restore placeholders back to original protected words
    for ph, word in placeholders.items():
        result = result.replace(ph, word)

    # 返回转换结果
    # Return conversion result
    return result


def _convert_cn_number(cn_str: str, cn_digits: dict, cn_units: dict):
    # 将中文数字字符串转换为整数
    # cn_str: 中文数字字符串（如"三百五十"）
    # cn_digits: 中文数字映射字典
    # cn_units: 中文单位映射字典
    # 返回转换后的整数，失败返回None
    # Convert Chinese number string to integer
    # cn_str: Chinese number string (e.g. "三百五十")
    # cn_digits: Chinese digit mapping dict
    # cn_units: Chinese unit mapping dict
    # Return converted integer, return None on failure

    # 如果字符串为空，返回None
    # If string is empty, return None
    if not cn_str:
        return None

    # 特殊处理：单独的"十"表示10
    # Special case: standalone "十" means 10
    if cn_str == '十':
        return 10

    # 初始化结果和临时值
    # Initialize result and temporary value
    result = 0
    temp = 0
    # 当前单位（万、亿等大单位）
    # Current unit (large units like 万, 亿)
    current_unit = 1

    # 遍历每个字符
    # Iterate through each character
    for char in cn_str:
        # 如果是数字字符
        # If it's a digit character
        if char in cn_digits:
            # 将数字加到临时值
            # Add digit to temporary value
            temp = cn_digits[char]
        # 如果是单位字符
        # If it's a unit character
        elif char in cn_units:
            # 获取单位对应的倍数
            # Get multiplier for the unit
            unit_value = cn_units[char]
            # 判断是否是大单位（万、亿）
            # Check if it's a large unit (万, 亿)
            if unit_value >= 10000:
                # 大单位：先将临时值乘以当前单位，再乘以大单位
                # Large unit: multiply temp by current unit, then by large unit
                result += (temp * current_unit) if temp else current_unit
                # 如果result为0但有临时值，用临时值
                # If result is 0 but has temp, use temp
                if result == 0 and temp:
                    result = temp
                result *= unit_value
                # 重置临时值和当前单位
                # Reset temp and current unit
                temp = 0
                current_unit = 1
            else:
                # 小单位（十、百、千）
                # Small unit (十, 百, 千)
                # 如果临时值为0且单位是十，表示省略了"一"
                # If temp is 0 and unit is 十, means "一" is omitted
                if temp == 0 and unit_value == 10:
                    temp = 1
                # 将临时值乘以单位倍数
                # Multiply temp by unit multiplier
                current_unit = temp * unit_value
                # 重置临时值
                # Reset temp
                temp = 0
                # 累加到结果
                # Add to result
                result += current_unit
                current_unit = 1
        else:
            # 未知字符，返回None
            # Unknown character, return None
            return None

    # 处理剩余的临时值
    # Process remaining temp value
    result += temp

    # 返回转换结果
    # Return conversion result
    return result if result > 0 else None
