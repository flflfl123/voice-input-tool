# -*- coding: utf-8 -*-
# 文本后处理管线模块 - 整合所有文本处理步骤
# 处理顺序：去除末尾标点 → ITN数字转换 → 热词替换 → 正则替换 → LLM角色检测
# Text post-processing pipeline module - integrate all text processing steps
# Processing order: remove trailing punctuation -> ITN number conversion -> hotword replacement -> regex replacement -> LLM role detection

# 导入日志记录库
# Import logging library
import logging

# 从各子模块导入处理类
# Import processing classes from sub-modules
from .itn import chinese_to_num
from .hotword import HotwordManager
from .hot_rule import RuleCorrector
from .llm_handler import LLMHandler
from .diary import DiaryWriter

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


class TextProcessor:
    # 文本后处理管线类
    # 按顺序执行所有文本处理步骤
    # Text post-processing pipeline class
    # Execute all text processing steps in order

    def __init__(self, config: dict):
        # 初始化文本处理器
        # config: 配置字典
        # Initialize text processor
        # config: config dictionary

        # 保存配置引用
        # Save config reference
        self.config = config

        # 初始化热词管理器（如果启用）
        # Initialize hotword manager (if enabled)
        if config.get("hot_enabled", True):
            threshold = config.get("hot_threshold", 0.85)
            self._hotword = HotwordManager(threshold=threshold)
        else:
            self._hotword = None

        # 初始化正则规则替换器（如果启用）
        # Initialize regex rule corrector (if enabled)
        if config.get("hot_rule_enabled", True):
            self._rule = RuleCorrector()
        else:
            self._rule = None

        # 初始化LLM处理器（如果启用）
        # Initialize LLM handler (if enabled)
        if config.get("llm_enabled", False):
            self._llm = LLMHandler(config)
        else:
            self._llm = None

        # 初始化日记写入器（如果启用）
        # Initialize diary writer (if enabled)
        if config.get("diary_enabled", True):
            self._diary = DiaryWriter()
        else:
            self._diary = None

        # 记录初始化日志
        # Log initialization
        logger.info("文本处理: 初始化完成 (热词=%s, 正则=%s, LLM=%s, 日记=%s)",
                    self._hotword is not None,
                    self._rule is not None,
                    self._llm is not None,
                    self._diary is not None)

    # 动态口令映射表
    # 口令 → 对应操作
    # Dynamic command mapping table
    # Command → corresponding action
    COMMANDS = {
        "撤销": "__UNDO__",
        "换行": "__NEWLINE__",
        "回车": "__NEWLINE__",
        "退格": "__BACKSPACE__",
        "删除": "__BACKSPACE__",
    }

    def process(self, text: str, llm_callback=None) -> str:
        # 处理文本：按顺序执行所有处理步骤
        # 第0步：检测动态口令（撤销、换行等）
        # 第1步：去除末尾逗号和句号
        # 第2步：ITN数字转换
        # 第3步：热词替换
        # 第4步：正则规则替换
        # 第5步：LLM角色检测
        # 第6步：写入日记
        # text: 输入文本
        # llm_callback: LLM结果回调函数
        # 返回处理后的文本（特殊口令返回控制字符串）
        # Process text: execute all processing steps in order
        # Step 0: Detect dynamic commands (undo, newline, etc.)
        # Step 1: Remove trailing commas and periods
        # Step 2: ITN number conversion
        # Step 3: Hotword replacement
        # Step 4: Regex rule replacement
        # Step 5: LLM role detection
        # Step 6: Write to diary
        # text: input text
        # llm_callback: LLM result callback
        # Return processed text (special commands return control strings)

        # 如果文本为空，直接返回
        # If text is empty, return directly
        if not text or not text.strip():
            return text

        # 第0步：检测动态口令
        # Step 0: Detect dynamic commands
        command = self._detect_command(text)
        if command:
            # 记录口令检测日志
            # Log command detection
            logger.info("文本处理: 检测到动态口令 '%s' -> '%s'", text, command)
            # 写入日记（记录口令操作）
            # Write to diary (record command operation)
            if self._diary:
                import time
                self._diary.write(f"[口令] {text}", timestamp=time.time())
            # 返回控制字符串
            # Return control string
            return command

        # 第1步：去除末尾逗号和句号（如果启用）
        # Step 1: Remove trailing commas and periods (if enabled)
        if self.config.get("remove_trailing_punct", True):
            text = self._remove_trailing_punctuation(text)

        # 第2步：ITN数字转换（如果启用）
        # Step 2: ITN number conversion (if enabled)
        if self.config.get("itn_enabled", True):
            text = chinese_to_num(text)

        # 第2.5步：去除语气词（如果启用，独立于 LLM 的纯文本过滤）
        # Step 2.5: Remove filler words (if enabled, independent pure text filter, no LLM dependency)
        if self.config.get("llm_remove_filler", False):
            text = self._remove_filler_words(text)

        # 第3步：热词替换（如果启用）
        # Step 3: Hotword replacement (if enabled)
        if self._hotword:
            text = self._hotword.substitute(text)

        # 第4步：正则规则替换（如果启用）
        # Step 4: Regex rule replacement (if enabled)
        if self._rule:
            text = self._rule.substitute(text)

        # 第5步：LLM角色检测和处理（如果启用）
        # Step 5: LLM role detection and processing (if enabled)
        if self._llm:
            # 检测是否匹配角色，如果匹配则由LLM处理
            # Detect if matches a role, if so LLM processes it
            handled = self._llm.process(text, callback=llm_callback)
            if handled:
                # LLM已处理，返回空字符串（结果通过回调返回）
                # LLM processed, return empty string (result returned via callback)
                return ""

        # 第6步：写入日记（如果启用）
        # Step 6: Write to diary (if enabled)
        if self._diary:
            # 导入时间库获取当前时间戳
            # Import time library to get current timestamp
            import time
            self._diary.write(text, timestamp=time.time())

        # 返回处理后的文本
        # Return processed text
        return text

    # 常见中文语气词/口头语模式（用于纯文本过滤，不依赖 LLM）
    # Common Chinese filler words patterns (pure text filter, no LLM dependency)
    # ponytail: 正则模式，如需支持更多语言可扩展
    _FILLER_PATTERNS = None  # 延迟编译，避免模块加载时依赖 re

    @classmethod
    def _get_filler_patterns(cls):
        # 延迟编译去除语气词的正则模式（只编译一次）
        # Lazy compile filler word regex patterns (compile once)
        if cls._FILLER_PATTERNS is None:
            import re
            # 匹配独立的语气词（前后不是同类型字符，避免误删"嗯好"→"好"）
            # Match standalone filler words (not between similar chars, avoid "嗯好"→"好")
            cls._FILLER_PATTERNS = re.compile(
                r'(?:^|(?<=[，。、！？\s]))'  # 开头或标点/空格后
                r'(?:呃|啊|嗯|哦|唉|诶|额|唔|欸|呣)'  # 语气词
                r'(?=(?:[，。、！？\s]|$))'  # 后面是标点/空格/结尾
            )
        return cls._FILLER_PATTERNS

    def _remove_filler_words(self, text: str) -> str:
        # 去除文本中的无意义语气词/口头语（纯文本过滤，不依赖 LLM）
        # 只去除填充停顿的语气词（呃、啊、嗯等），保留有实际意义的词
        # 例如："呃，我想一下" → "，我想一下"
        # Remove meaningless filler words from text (pure text filter, no LLM)
        # Only remove fillers for pauses (uh, ah, um), keep meaningful words
        # E.g. "呃，我想一下" → "，我想一下"
        pattern = self._get_filler_patterns()
        result = pattern.sub('', text)
        # 清理可能留下的连续标点（如"呃，嗯，" → "，"）
        # Clean up possible consecutive punctuation left behind
        import re
        result = re.sub(r'([，。、！？]){2,}', r'\1', result)
        return result.strip()

    def _detect_command(self, text: str) -> str:
        # 检测文本是否为动态口令
        # text: 输入文本
        # 返回控制字符串，非口令返回空字符串
        # Detect if text is a dynamic command
        # text: input text
        # Return control string, empty string if not a command

        # 去除首尾空白和标点
        # Strip whitespace and punctuation
        cleaned = text.strip().strip('，。、！？,.!')
        # 检查是否匹配口令
        # Check if matches a command
        for cmd_text, cmd_code in self.COMMANDS.items():
            if cleaned == cmd_text:
                # 匹配到口令，返回控制字符串
                # Matched command, return control string
                return cmd_code
        # 未匹配口令，返回空字符串
        # No command matched, return empty string
        return ""

    def _remove_trailing_punctuation(self, text: str) -> str:
        # 去除文本末尾的逗号和句号
        # text: 输入文本
        # 返回去除末尾标点后的文本
        # Remove trailing commas and periods from text
        # text: input text
        # Return text with trailing punctuation removed

        # 定义要去除的末尾标点字符
        # Define trailing punctuation characters to remove
        trailing_punct = '，。、！？,.!?'
        # 循环去除末尾标点
        # Loop to remove trailing punctuation
        while text and text[-1] in trailing_punct:
            text = text[:-1]
        # 返回处理后的文本
        # Return processed text
        return text

    def reload_hotwords(self) -> int:
        # 重新加载热词文件
        # 返回加载的热词数量
        # Reload hotword file
        # Return number of loaded hotwords
        if self._hotword:
            return self._hotword.reload()
        return 0

    def reload_rules(self) -> int:
        # 重新加载正则规则文件
        # 返回加载的规则数量
        # Reload regex rule file
        # Return number of loaded rules
        if self._rule:
            return self._rule.reload()
        return 0

    def add_hotword(self, word: str, replacement: str = None):
        # 添加热词
        # word: 热词
        # replacement: 替换词
        # Add hotword
        # word: hotword
        # replacement: replacement
        if self._hotword:
            self._hotword.add_hotword(word, replacement)

    def clear_llm_history(self):
        # 清除LLM对话历史
        # Clear LLM conversation history
        if self._llm:
            self._llm.clear_history()

    def get_last_result(self) -> str:
        # 获取最近一次识别结果（用于复制）
        # 返回最近的识别结果文本
        # Get most recent recognition result (for copying)
        # Return most recent recognition result text
        return self._last_result if hasattr(self, '_last_result') else ""

    def set_last_result(self, text: str):
        # 设置最近一次识别结果
        # text: 识别结果文本
        # Set most recent recognition result
        # text: recognition result text
        self._last_result = text
