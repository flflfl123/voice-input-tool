# -*- coding: utf-8 -*-
# ITN增强规则模块 - 处理cn2an无法覆盖的中文数字转换场景
# 包括：范围/约数、日期、百分比、分数等
# 参考自 CapsWriter-Offline 项目 (https://github.com/HaujetZhao/CapsWriter-Offline)
# CapsWriter-Offline 采用 MIT 协议开源，作者：HaujetZhao
# ITN enhanced rules module - handle Chinese number conversion scenarios
# that cn2an cannot cover, including: ranges/approx, dates, percentages, fractions
# Referenced from CapsWriter-Offline project's chinese_itn.py (MIT License)

# 导入正则表达式库
# Import regular expression library
import re
# 导入日志记录库
# Import logging library
import logging

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


def apply_enhanced_rules(text: str) -> str:
    # 应用增强ITN规则，处理cn2an无法覆盖的场景
    # 处理顺序：百分比 → 分数 → 范围/约数 → 日期年份
    # text: 输入文本
    # 返回转换后的文本
    # Apply enhanced ITN rules for scenarios cn2an cannot cover
    # Order: percentage → fraction → range/approx → date/year
    # text: input text
    # Return converted text

    # 如果文本为空，直接返回
    # If text is empty, return directly
    if not text:
        return text

    # 保存原始文本用于比较
    # Save original text for comparison
    original = text

    # ========== 1. 百分比转换 ==========
    # 「百分之三十」→「30%」，「百分之五点五」→「5.5%」
    # Percentage conversion
    text = _convert_percentage(text)

    # ========== 2. 分数转换 ==========
    # 「三分之二」→「2/3」，「二分之一」→「1/2」
    # Fraction conversion
    text = _convert_fraction(text)

    # ========== 3. 范围/约数转换 ==========
    # 「十五六个」→「15~16个」，「三四十个」→「30~40个」
    # Range/approximate number conversion
    text = _convert_range(text)

    # ========== 4. 日期年份转换 ==========
    # 「二零二四年」→「2024年」，「六月七日」→「6月7日」
    # Date/year conversion
    text = _convert_date(text)

    # 记录转换日志
    # Log conversion
    if text != original:
        logger.info("ITN增强: '%s' -> '%s'", original, text)

    # 返回转换结果
    # Return conversion result
    return text


# ========== 中文数字映射表 ==========
# ========== Chinese number mapping table ==========
_CN_DIGITS = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '两': 2, '〇': 0,
}


def _cn_digit_to_int(cn: str) -> int:
    # 单个中文数字字符转整数
    # cn: 中文数字字符
    # 返回对应整数，无法识别返回-1
    # Convert single Chinese digit character to integer
    # cn: Chinese digit character
    # Return corresponding integer, -1 if unrecognized
    return _CN_DIGITS.get(cn, -1)


def _cn_small_number_to_int(cn_str: str) -> int:
    # 将简短中文数字（0~99）转为整数
    # 支持「十五」「二十」「三」「十一」等
    # cn_str: 中文数字字符串
    # 返回对应整数，失败返回-1
    # Convert short Chinese number (0~99) to integer
    # Supports "十五" "二十" "三" "十一" etc.
    # cn_str: Chinese number string
    # Return corresponding integer, -1 on failure

    # 特殊处理：单独的「十」表示10
    # Special case: standalone "十" means 10
    if cn_str == '十':
        return 10

    # 中文单位映射
    # Chinese unit mapping
    units = {'十': 10, '百': 100}

    # 初始化结果
    # Initialize result
    result = 0
    # 当前临时值
    # Current temp value
    temp = 0

    # 遍历每个字符
    # Iterate each character
    for char in cn_str:
        # 如果是数字字符
        # If it's a digit character
        if char in _CN_DIGITS:
            # 记录数字
            # Record digit
            temp = _CN_DIGITS[char]
        # 如果是单位字符
        # If it's a unit character
        elif char in units:
            # 如果临时值为0且单位是十，省略了「一」
            # If temp is 0 and unit is 十, "一" is omitted
            if temp == 0 and char == '十':
                temp = 1
            # 累加临时值乘以单位
            # Add temp multiplied by unit
            result += temp * units[char]
            # 重置临时值
            # Reset temp
            temp = 0
        else:
            # 无法识别的字符，返回-1
            # Unrecognized character, return -1
            return -1

    # 处理剩余临时值
    # Process remaining temp value
    result += temp

    # 返回结果（0也合法，如「零」）
    # Return result (0 is also valid, e.g. "零")
    return result if result >= 0 else -1


def _convert_percentage(text: str) -> str:
    # 百分比转换：「百分之三十」→「30%」，「百分之五点五」→「5.5%」
    # Percentage conversion
    # 中文数字字符集（含小数点）
    # Chinese digit character set (including decimal point)
    cn_num_chars = '零一二三四五六七八九点两'

    def _replace_pct(match):
        # 替换单个百分比匹配
        # Replace single percentage match
        # 获取百分号后面的中文数字部分
        # Get Chinese number part after "百分之"
        num_str = match.group(1)
        # 尝试转换中文数字
        # Try to convert Chinese number
        # 处理小数：先按「点」分割
        # Handle decimal: split by "点" first
        if '点' in num_str:
            # 分割整数和小数部分
            # Split integer and decimal parts
            parts = num_str.split('点', 1)
            # 转换整数部分
            # Convert integer part
            int_val = _cn_small_number_to_int(parts[0])
            if int_val < 0:
                # 转换失败，返回原文
                # Conversion failed, return original
                return match.group(0)
            # 小数部分逐字转换
            # Convert decimal part character by character
            dec_str = ''
            for ch in parts[1]:
                d = _cn_digit_to_int(ch)
                if d < 0:
                    # 无法识别，返回原文
                    # Unrecognized, return original
                    return match.group(0)
                dec_str += str(d)
            # 组合结果
            # Combine result
            return f"{int_val}.{dec_str}%"
        else:
            # 没有小数，直接转换
            # No decimal, convert directly
            val = _cn_small_number_to_int(num_str)
            if val < 0:
                # 转换失败，返回原文
                # Conversion failed, return original
                return match.group(0)
            return f"{val}%"

    # 匹配「百分之」+ 中文数字
    # Match "百分之" + Chinese number
    pattern = r'百分之([' + cn_num_chars + ']+)'
    # 执行替换
    # Execute replacement
    return re.sub(pattern, _replace_pct, text)


def _convert_fraction(text: str) -> str:
    # 分数转换：「三分之二」→「2/3」，「二分之一」→「1/2」
    # Fraction conversion
    # 中文数字字符集
    # Chinese digit character set
    cn_num_chars = '零一二三四五六七八九十百两'

    def _replace_frac(match):
        # 替换单个分数匹配
        # Replace single fraction match
        # 获取分母和分子
        # Get denominator and numerator
        denom_str = match.group(1)
        numer_str = match.group(2)
        # 转换分母
        # Convert denominator
        denom = _cn_small_number_to_int(denom_str)
        # 转换分子
        # Convert numerator
        numer = _cn_small_number_to_int(numer_str)
        # 检查转换是否成功
        # Check if conversion succeeded
        if denom <= 0 or numer < 0:
            # 转换失败，返回原文
            # Conversion failed, return original
            return match.group(0)
        # 返回分数格式
        # Return fraction format
        return f"{numer}/{denom}"

    # 匹配「X分之Y」格式
    # Match "X分之Y" format
    pattern = r'([' + cn_num_chars + r']+)分之([' + cn_num_chars + r']+)'
    # 执行替换
    # Execute replacement
    return re.sub(pattern, _replace_frac, text)


def _convert_range(text: str) -> str:
    # 范围/约数转换：「十五六个」→「15~16个」，「三四十个」→「30~40个」
    # Range/approximate number conversion
    # 中文数字字符集（不含单位，用于个位数匹配）
    # Chinese digit character set (without units, for single digit matching)
    cn_digits_only = '零一二三四五六七八九两'

    def _replace_range_1(match):
        # 替换「X十Y六个」格式：如「十五六个」→「15~16个」
        # Replace "X十Y六个" format: e.g. "十五六个" -> "15~16个"
        # 获取十位数字（可能为空，表示1）
        # Get tens digit (may be empty, meaning 1)
        tens_str = match.group(1) or '一'
        # 获取个位数字
        # Get ones digit
        ones_str = match.group(2)
        # 转换十位
        # Convert tens
        tens = _cn_digit_to_int(tens_str)
        # 转换个位
        # Convert ones
        ones = _cn_digit_to_int(ones_str)
        # 检查转换是否成功
        # Check if conversion succeeded
        if tens < 0 or ones < 0:
            # 转换失败，返回原文
            # Conversion failed, return original
            return match.group(0)
        # 计算范围：如「十五六」= 15~16
        # Calculate range: e.g. "十五六" = 15~16
        low = tens * 10 + ones
        high = low + 1
        # 返回范围格式
        # Return range format
        return f"{low}~{high}"

    # 匹配「X十Y六个」格式（X可空，Y为个位数字）
    # Match "X十Y六个" format (X may be empty, Y is ones digit)
    pattern1 = r'([' + cn_digits_only + r']?)十([' + cn_digits_only + r'])[五六七]'
    text = re.sub(pattern1, _replace_range_1, text)

    def _replace_range_2(match):
        # 替换「X四十个」格式：如「三四十个」→「30~40个」
        # Replace "X四十个" format: e.g. "三四十个" -> "30~40个"
        # 获取十位数字
        # Get tens digit
        tens_str = match.group(1)
        # 转换十位
        # Convert tens
        tens = _cn_digit_to_int(tens_str)
        # 检查转换是否成功
        # Check if conversion succeeded
        if tens < 0:
            # 转换失败，返回原文
            # Conversion failed, return original
            return match.group(0)
        # 计算范围：如「三四」= 30~40
        # Calculate range: e.g. "三四" = 30~40
        low = tens * 10
        high = (tens + 1) * 10
        # 返回范围格式
        # Return range format
        return f"{low}~{high}"

    # 匹配「XY十个」格式（X和Y为连续个位数字，表示约数范围）
    # Match "XY十个" format (X and Y are consecutive digits, meaning approx range)
    pattern2 = r'([' + cn_digits_only + r'])([' + cn_digits_only + r'])十'
    text = re.sub(pattern2, _replace_range_2, text)

    # 返回转换结果
    # Return conversion result
    return text


def _convert_date(text: str) -> str:
    # 日期年份转换：「二零二四年」→「2024年」，「六月七日」→「6月7日」
    # Date/year conversion
    # 中文数字字符集（含〇）
    # Chinese digit character set (including 〇)
    cn_year_chars = '零一二三四五六七八九〇两'

    def _replace_year(match):
        # 替换年份格式：「二零二四」→「2024」
        # Replace year format: "二零二四" -> "2024"
        # 获取中文年份字符串
        # Get Chinese year string
        year_str = match.group(1)
        # 逐字转换
        # Convert character by character
        result = ''
        for ch in year_str:
            d = _cn_digit_to_int(ch)
            if d < 0:
                # 无法识别，返回原文
                # Unrecognized, return original
                return match.group(0)
            result += str(d)
        # 返回阿拉伯数字年份
        # Return Arabic number year
        return result

    # 匹配4位中文数字+「年」：如「二零二四年」
    # Match 4-digit Chinese number + "年": e.g. "二零二四年"
    pattern_year = r'([' + cn_year_chars + r']{4})年'
    text = re.sub(pattern_year, _replace_year, text)

    def _replace_month_day(match):
        # 替换月日格式：「六月七日」→「6月7日」
        # Replace month/day format: "六月七日" -> "6月7日"
        # 获取月份和日期字符串
        # Get month and day strings
        month_str = match.group(1)
        day_str = match.group(2)
        # 转换月份
        # Convert month
        month = _cn_small_number_to_int(month_str)
        # 转换日期
        # Convert day
        day = _cn_small_number_to_int(day_str)
        # 检查转换是否成功
        # Check if conversion succeeded
        if month <= 0 or day <= 0:
            # 转换失败，返回原文
            # Conversion failed, return original
            return match.group(0)
        # 返回阿拉伯数字月日
        # Return Arabic number month/day
        return f"{month}月{day}日"

    # 匹配中文月日：如「六月七日」「十二月三日」
    # Match Chinese month/day: e.g. "六月七日" "十二月三日"
    cn_num_chars = '零一二三四五六七八九十两'
    pattern_md = r'([' + cn_num_chars + r']+)月([' + cn_num_chars + r']+)日'
    text = re.sub(pattern_md, _replace_month_day, text)

    # 返回转换结果
    # Return conversion result
    return text
