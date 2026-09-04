# -*- coding: utf-8 -*-
# 热词替换模块 - 通过音素模糊匹配替换ASR识别不准的偏僻词
# 读取 config/hot.txt 中的热词，将文本转为拼音序列，计算相似度进行替换
# 参考自 CapsWriter-Offline 项目 (https://github.com/HaujetZhao/CapsWriter-Offline)
# CapsWriter-Offline 采用 MIT 协议开源，作者：HaujetZhao
# Hotword replacement module - replace misrecognized rare words via phoneme fuzzy matching
# Read hotwords from config/hot.txt, convert text to pinyin sequences, calculate similarity for replacement
# Referenced from CapsWriter-Offline project's hot_phoneme.py

# 导入日志记录库
# Import logging library
import logging
# 导入线程锁
# Import thread lock
from threading import Lock
# 导入路径处理库
# Import path processing library
from pathlib import Path

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 热词文件路径 ==========
# ========== Hotword file path ==========
HOTWORD_FILE = Path(__file__).parent.parent / "config" / "hot.txt"


def _get_pinyin(text: str) -> list:
    # 获取文本的拼音列表
    # text: 输入文本
    # 返回拼音字符串列表（每个字符对应一个拼音）
    # Get pinyin list of text
    # text: input text
    # Return pinyin string list (one pinyin per character)

    try:
        # 尝试使用 pypinyin 库获取拼音
        # Try using pypinyin library to get pinyin
        from pypinyin import pinyin, Style
        # 获取不带声调的拼音
        # Get pinyin without tone
        result = pinyin(text, style=Style.NORMAL)
        # 将嵌套列表展平为一维列表
        # Flatten nested list to one-dimensional list
        return [item[0] for item in result]
    except ImportError:
        # pypinyin 未安装，使用简单首字母回退
        # pypinyin not installed, use simple initial fallback
        logger.warning("热词: pypinyin 库未安装，热词替换功能不可用")
        return []


def _edit_distance(s1: list, s2: list) -> float:
    # 计算两个拼音序列之间的编辑距离相似度
    # s1: 第一个拼音序列
    # s2: 第二个拼音序列
    # 返回相似度（0.0~1.0，1.0表示完全相同）
    # Calculate edit distance similarity between two pinyin sequences
    # s1: first pinyin sequence
    # s2: second pinyin sequence
    # Return similarity (0.0~1.0, 1.0 means identical)

    # 如果两个序列都为空，相似度为1
    # If both sequences are empty, similarity is 1
    if not s1 and not s2:
        return 1.0
    # 如果其中一个为空，相似度为0
    # If one is empty, similarity is 0
    if not s1 or not s2:
        return 0.0

    # 获取序列长度
    # Get sequence lengths
    len1, len2 = len(s1), len(s2)
    # 创建距离矩阵（len1+1 行，len2+1 列）
    # Create distance matrix (len1+1 rows, len2+1 columns)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    # 初始化第一行和第一列
    # Initialize first row and first column
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    # 动态规划计算编辑距离
    # Dynamic programming to calculate edit distance
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            # 如果当前拼音相同，不需要操作
            # If current pinyins are same, no operation needed
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # 取插入、删除、替换的最小值加1
                # Take minimum of insert, delete, replace plus 1
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 删除 / Delete
                    dp[i][j - 1],      # 插入 / Insert
                    dp[i - 1][j - 1],  # 替换 / Replace
                )

    # 计算相似度：1 - 编辑距离 / 最大长度
    # Calculate similarity: 1 - edit distance / max length
    max_len = max(len1, len2)
    similarity = 1.0 - dp[len1][len2] / max_len
    return similarity


class HotwordManager:
    # 热词管理器类
    # 从 hot.txt 加载热词，对文本进行音素模糊匹配替换
    # Hotword manager class
    # Load hotwords from hot.txt, perform phoneme fuzzy matching replacement on text

    def __init__(self, hotword_path: str = None, threshold: float = 0.85):
        # 初始化热词管理器
        # hotword_path: 热词文件路径，默认为 config/hot.txt
        # threshold: 精确匹配阈值（0.0~1.0），默认0.85
        # Initialize hotword manager
        # hotword_path: hotword file path, default to config/hot.txt
        # threshold: exact match threshold (0.0~1.0), default 0.85

        # 保存热词文件路径
        # Save hotword file path
        self._hotword_path = Path(hotword_path) if hotword_path else HOTWORD_FILE
        # 保存匹配阈值
        # Save match threshold
        self._threshold = threshold
        # 存储热词列表，每项为 (热词, 替换词, 拼音列表) 的元组
        # Store hotword list, each item is a tuple of (hotword, replacement, pinyin_list)
        self._hotwords = []
        # 线程锁，保护 _hotwords 的线程安全
        # Thread lock, protect thread safety of _hotwords
        self._lock = Lock()
        # 记录初始化日志
        # Log initialization
        logger.info("热词: 初始化，热词文件: %s，阈值: %.2f", self._hotword_path, self._threshold)
        # 启动时自动加载热词文件
        # Auto-load hotword file on startup
        self.load_hotwords()

    def load_hotwords(self) -> int:
        # 从文件加载热词
        # 返回加载的热词数量
        # Load hotwords from file
        # Return number of loaded hotwords

        # 检查热词文件是否存在
        # Check if hotword file exists
        if not self._hotword_path.exists():
            # 文件不存在，记录日志并返回0
            # File not found, log and return 0
            logger.info("热词: 热词文件不存在: %s", self._hotword_path)
            return 0

        try:
            # 以UTF-8编码读取热词文件
            # Read hotword file with UTF-8 encoding
            with open(self._hotword_path, "r", encoding="utf-8") as f:
                hotword_text = f.read()
            # 调用更新热词函数
            # Call update hotwords function
            count = self.update_hotwords(hotword_text)
            # 记录加载成功日志
            # Log load success
            logger.info("热词: 已加载 %d 个热词", count)
            # 返回热词数量
            # Return hotword count
            return count
        except Exception as e:
            # 记录加载失败日志
            # Log load failure
            logger.error("热词: 加载热词文件失败: %s", e)
            return 0

    def update_hotwords(self, hotword_text: str) -> int:
        # 解析热词文本并更新热词列表
        # hotword_text: 热词文本内容
        # 返回解析到的热词数量
        # Parse hotword text and update hotword list
        # hotword_text: hotword text content
        # Return number of parsed hotwords

        # 创建新的热词列表
        # Create new hotword list
        new_hotwords = []
        # 按行分割热词文本
        # Split hotword text by lines
        for line in hotword_text.splitlines():
            # 去除首尾空白
            # Strip leading/trailing whitespace
            line = line.strip()
            # 跳过空行和注释行
            # Skip empty lines and comment lines
            if not line or line.startswith('#'):
                continue
            # 按等号分割，最多分割一次
            # Split by equals sign, at most once
            parts = line.split(' = ', 1)
            if len(parts) == 2:
                # 获取热词（等号左边）
                # Get hotword (left of equals)
                word = parts[0].strip()
                # 获取替换词（等号右边）
                # Get replacement (right of equals)
                replacement = parts[1].strip()
            else:
                # 没有等号，热词和替换词相同
                # No equals sign, hotword and replacement are the same
                word = line
                replacement = line

            # 获取热词的拼音序列
            # Get pinyin sequence of hotword
            pinyin_list = _get_pinyin(word)
            # 如果拼音列表不为空，添加到新热词列表
            # If pinyin list is not empty, add to new hotword list
            if pinyin_list:
                new_hotwords.append((word, replacement, pinyin_list))

        # 线程安全地更新热词列表
        # Thread-safely update hotword list
        with self._lock:
            self._hotwords = new_hotwords
        # 返回热词数量
        # Return hotword count
        return len(new_hotwords)

    def substitute(self, text: str) -> str:
        # 对文本应用热词替换
        # 核心逻辑：将文本转为拼音序列，滑动窗口匹配热词拼音，
        # 根据字符位置替换匹配到的子串（而非在原文中查找热词字符串）
        # 长热词优先匹配，避免短热词"截胡"
        # text: 输入文本
        # 返回替换后的文本
        # Apply hotword replacement to text
        # Core logic: convert text to pinyin sequence, sliding window match hotword pinyin,
        # replace matched substring by character position (not by searching hotword string in text)
        # Longer hotwords have priority to avoid short hotword "hijacking"
        # text: input text
        # Return replaced text

        # 如果文本为空或没有热词，直接返回原文
        # If text is empty or no hotwords, return original text
        if not text or not self._hotwords:
            return text

        # 线程安全地获取热词副本
        # Thread-safely get a copy of hotwords
        with self._lock:
            hotwords = self._hotwords.copy()

        # 获取输入文本的拼音序列
        # Get pinyin sequence of input text
        text_pinyin = _get_pinyin(text)
        # 如果拼音列表为空（pypinyin未安装），返回原文
        # If pinyin list is empty (pypinyin not installed), return original text
        if not text_pinyin:
            return text

        # 收集所有匹配结果：(起始拼音索引, 结束拼音索引, 替换词, 相似度)
        # Collect all match results: (start pinyin index, end pinyin index, replacement, similarity)
        matches = []

        # 按热词拼音长度降序排列，长热词优先匹配
        # Sort by hotword pinyin length descending, longer hotwords first
        sorted_hotwords = sorted(hotwords, key=lambda x: len(x[2]), reverse=True)

        # 遍历所有热词，尝试匹配
        # Iterate all hotwords, try to match
        for word, replacement, word_pinyin in sorted_hotwords:
            # 获取热词拼音长度
            # Get hotword pinyin length
            word_len = len(word_pinyin)
            # 在文本拼音序列中滑动窗口匹配
            # Sliding window match in text pinyin sequence
            for i in range(len(text_pinyin) - word_len + 1):
                # 提取当前窗口的拼音子序列
                # Extract pinyin subsequence of current window
                window = text_pinyin[i:i + word_len]
                # 计算相似度
                # Calculate similarity
                similarity = _edit_distance(window, word_pinyin)
                # 如果相似度超过阈值，记录匹配结果
                # If similarity exceeds threshold, record match result
                if similarity >= self._threshold:
                    # 记录匹配的起止拼音索引和替换词
                    # Record matched start/end pinyin index and replacement
                    matches.append((i, i + word_len, replacement, similarity, word))
                    # 匹配到后跳出内层循环（每个热词只匹配第一个）
                    # Break inner loop after match (each hotword matches first only)
                    break

        # 如果没有匹配，直接返回原文
        # If no matches, return original text
        if not matches:
            return text

        # 解决重叠匹配：保留相似度最高的匹配，去除重叠
        # Resolve overlapping matches: keep highest similarity, remove overlaps
        # 按相似度降序排列
        # Sort by similarity descending
        matches.sort(key=lambda x: x[3], reverse=True)
        # 已被占用的拼音索引集合
        # Set of occupied pinyin indices
        occupied = set()
        # 最终保留的匹配列表
        # Final kept matches list
        final_matches = []
        for start, end, replacement, similarity, word in matches:
            # 检查该匹配范围是否与已有匹配重叠
            # Check if this match range overlaps with existing matches
            overlap = False
            for idx in range(start, end):
                if idx in occupied:
                    overlap = True
                    break
            if not overlap:
                # 不重叠，保留该匹配
                # No overlap, keep this match
                final_matches.append((start, end, replacement, similarity, word))
                # 标记占用范围
                # Mark occupied range
                for idx in range(start, end):
                    occupied.add(idx)

        # 按起始位置升序排列，方便从后往前替换（避免索引偏移）
        # Sort by start position ascending, replace from end to start (avoid index shift)
        final_matches.sort(key=lambda x: x[0], reverse=True)

        # 将文本转为字符列表，方便按位置替换
        # Convert text to character list for position-based replacement
        chars = list(text)

        # 从后往前替换，避免前面的替换影响后面的索引
        # Replace from end to start to avoid earlier replacements affecting later indices
        for start, end, replacement, similarity, word in final_matches:
            # 计算文本中对应的起止字符位置
            # Calculate corresponding start/end character positions in text
            # 拼音索引与字符索引一一对应（pypinyin每个字符一个拼音）
            # Pinyin index corresponds one-to-one with character index
            char_start = start
            char_end = end
            # 确保索引不越界
            # Ensure indices don't go out of bounds
            if char_start < 0 or char_end > len(chars):
                continue
            # 记录替换日志
            # Log replacement
            if similarity >= 1.0:
                logger.info("热词: 精确替换 '%s' -> '%s'", word, replacement)
            else:
                logger.info("热词: 模糊替换 '%s' -> '%s' (相似度: %.2f)", word, replacement, similarity)
            # 替换字符：删除原字符，插入替换词
            # Replace characters: remove original, insert replacement
            chars[char_start:char_end] = list(replacement)

        # 将字符列表拼接回字符串
        # Join character list back to string
        return ''.join(chars)

    def reload(self) -> int:
        # 重新加载热词文件（用于热重载）
        # 返回加载的热词数量
        # Reload hotword file (for hot reload)
        # Return number of loaded hotwords
        return self.load_hotwords()

    def add_hotword(self, word: str, replacement: str = None):
        # 添加单个热词到文件
        # word: 热词
        # replacement: 替换词，如果为空则与热词相同
        # Add single hotword to file
        # word: hotword
        # replacement: replacement, if empty same as hotword

        # 如果没有指定替换词，替换词与热词相同
        # If no replacement specified, same as hotword
        if replacement is None:
            replacement = word
        # 构建要写入的行
        # Build line to write
        line = f"{word} = {replacement}\n"
        try:
            # 以追加模式打开热词文件
            # Open hotword file in append mode
            with open(self._hotword_path, "a", encoding="utf-8") as f:
                f.write(line)
            # 重新加载热词
            # Reload hotwords
            self.load_hotwords()
            # 记录添加成功日志
            # Log add success
            logger.info("热词: 已添加热词 '%s' -> '%s'", word, replacement)
        except Exception as e:
            # 记录添加失败日志
            # Log add failure
            logger.error("热词: 添加热词失败: %s", e)
