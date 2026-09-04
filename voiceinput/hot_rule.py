# -*- coding: utf-8 -*-
# 正则规则替换模块 - 读取 hot-rule.txt 中的规则进行文本替换
# 支持正则表达式和简单等号规则两种格式
# 参考自 CapsWriter-Offline 项目 (https://github.com/HaujetZhao/CapsWriter-Offline)
# CapsWriter-Offline 采用 MIT 协议开源，作者：HaujetZhao
# Regex rule replacement module - read rules from hot-rule.txt for text replacement
# Supports both regex and simple equality rule formats
# Referenced from CapsWriter-Offline project's hot_rule.py

# 导入正则表达式库
# Import regular expression library
import re
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

# ========== 规则文件路径 ==========
# ========== Rule file path ==========
# 规则文件位于 config 目录下
# Rule file is in config directory
RULE_FILE = Path(__file__).parent.parent / "config" / "hot-rule.txt"


class RuleCorrector:
    # 正则规则替换器类
    # 从 hot-rule.txt 读取规则，对文本进行正则替换
    # Regex rule corrector class
    # Read rules from hot-rule.txt, perform regex replacement on text

    def __init__(self, rule_path: str = None):
        # 初始化正则规则替换器
        # rule_path: 规则文件路径，默认为 config/hot-rule.txt
        # Initialize regex rule corrector
        # rule_path: rule file path, default to config/hot-rule.txt

        # 保存规则文件路径
        # Save rule file path
        self._rule_path = Path(rule_path) if rule_path else RULE_FILE
        # 存储规则列表，每项为 (pattern, replacement, is_regex) 的元组
        # Store rule list, each item is (pattern, replacement, is_regex) tuple
        self._rules = []
        # 线程锁，保护 _rules 的线程安全
        # Thread lock, protect thread safety of _rules
        self._lock = Lock()
        # 记录初始化日志
        # Log initialization
        logger.info("正则替换: 初始化，规则文件: %s", self._rule_path)
        # 启动时自动加载规则文件
        # Auto-load rule file on startup
        self.load_rules()

    def load_rules(self) -> int:
        # 从文件加载正则替换规则
        # 返回加载的规则数量
        # Load regex replacement rules from file
        # Return number of loaded rules

        # 检查规则文件是否存在
        # Check if rule file exists
        if not self._rule_path.exists():
            # 文件不存在，记录日志并返回0
            # File not found, log and return 0
            logger.info("正则替换: 规则文件不存在: %s", self._rule_path)
            return 0

        try:
            # 以UTF-8编码读取规则文件
            # Read rule file with UTF-8 encoding
            with open(self._rule_path, "r", encoding="utf-8") as f:
                rule_text = f.read()
            # 调用更新规则函数
            # Call update rules function
            count = self.update_rules(rule_text)
            # 记录加载成功日志
            # Log load success
            logger.info("正则替换: 已加载 %d 条规则", count)
            # 返回规则数量
            # Return rule count
            return count
        except Exception as e:
            # 记录加载失败日志
            # Log load failure
            logger.error("正则替换: 加载规则文件失败: %s", e)
            return 0

    def update_rules(self, rule_text: str) -> int:
        # 解析规则文本并更新规则列表
        # 支持三种分隔符格式：= 、=> 、→
        # 区分正则规则和纯文本规则：纯文本规则用str.replace，正则规则用re.sub
        # rule_text: 规则文本内容
        # 返回解析到的规则数量
        # Parse rule text and update rule list
        # Supports three separator formats: = , => , →
        # Distinguishes regex rules and plain text rules:
        #   plain text rules use str.replace, regex rules use re.sub
        # rule_text: rule text content
        # Return number of parsed rules

        # 创建新的规则列表，每项为 (pattern, replacement, is_regex)
        # Create new rule list, each item is (pattern, replacement, is_regex)
        new_rules = []
        # 按行分割规则文本
        # Split rule text by lines
        for line in rule_text.splitlines():
            # 去除首尾空白
            # Strip leading/trailing whitespace
            line = line.strip()
            # 跳过空行和注释行（以#开头）
            # Skip empty lines and comment lines (starting with #)
            if not line or line.startswith('#'):
                continue
            # 按分隔符分割，优先匹配 => ，然后 → ，最后 =
            # Split by separator, prefer => , then → , finally =
            pattern = None
            replacement = None
            # 尝试按 => 分割
            # Try splitting by =>
            if ' => ' in line:
                parts = line.split(' => ', 1)
                pattern = parts[0].strip()
                replacement = parts[1].strip()
            # 尝试按 → 分割
            # Try splitting by →
            elif ' → ' in line:
                parts = line.split(' → ', 1)
                pattern = parts[0].strip()
                replacement = parts[1].strip()
            # 尝试按 = 分割
            # Try splitting by =
            elif ' = ' in line:
                parts = line.split(' = ', 1)
                pattern = parts[0].strip()
                replacement = parts[1].strip()
            # 如果没有分隔符，跳过该行
            # If no separator, skip this line
            if pattern is None or replacement is None:
                continue
            # 判断是否为正则规则：模式中包含正则特殊字符
            # Determine if it's a regex rule: pattern contains regex special chars
            # 正则特殊字符：( ) [ ] { } \d \w \s \S + * ? ^ $ | .
            # Regex special chars: ( ) [ ] { } \d \w \s \S + * ? ^ $ | .
            regex_chars = r'()[\]{}\\dwsDS+*?^$|.'
            # 检查模式中是否包含正则特殊字符
            # Check if pattern contains regex special chars
            is_regex = any(c in pattern for c in regex_chars)
            if is_regex:
                # 正则规则：尝试编译验证
                # Regex rule: try to compile for validation
                try:
                    re.compile(pattern)
                except re.error as e:
                    # 正则编译失败，记录警告并跳过
                    # Regex compilation failed, log warning and skip
                    logger.warning("正则替换: 规则编译失败 '%s': %s", pattern, e)
                    continue
            # 添加到新规则列表
            # Add to new rule list
            new_rules.append((pattern, replacement, is_regex))

        # 线程安全地更新规则列表
        # Thread-safely update rule list
        with self._lock:
            self._rules = new_rules
        # 返回规则数量
        # Return rule count
        return len(new_rules)

    def substitute(self, text: str) -> str:
        # 对文本应用所有替换规则
        # 纯文本规则用 str.replace，正则规则用 re.sub
        # text: 输入文本
        # 返回替换后的文本
        # Apply all replacement rules to text
        # Plain text rules use str.replace, regex rules use re.sub
        # text: input text
        # Return replaced text

        # 如果文本为空或没有规则，直接返回原文
        # If text is empty or no rules, return original text
        if not text or not self._rules:
            return text

        # 线程安全地获取规则副本
        # Thread-safely get a copy of rules
        with self._lock:
            rules = self._rules.copy()

        # 初始化结果为输入文本
        # Initialize result as input text
        result = text
        # 遍历所有规则并应用
        # Iterate all rules and apply
        for pattern, replacement, is_regex in rules:
            try:
                if is_regex:
                    # 正则规则：使用 re.sub 替换
                    # Regex rule: use re.sub for replacement
                    new_result = re.sub(pattern, replacement, result)
                else:
                    # 纯文本规则：使用 str.replace 替换（更安全、更快）
                    # Plain text rule: use str.replace (safer, faster)
                    new_result = result.replace(pattern, replacement)
                # 如果替换结果有变化，记录日志
                # If replacement result changed, log it
                if new_result != result:
                    rule_type = "正则" if is_regex else "文本"
                    logger.info("正则替换: [%s] '%s' -> '%s' (规则: %s)", rule_type, result, new_result, pattern)
                    result = new_result
            except Exception as e:
                # 替换失败时记录警告，继续下一条规则
                # Log warning on replacement failure, continue to next rule
                logger.warning("正则替换: 应用规则失败 '%s': %s", pattern, e)

        # 返回替换结果
        # Return replacement result
        return result

    def reload(self) -> int:
        # 重新加载规则文件（用于热重载）
        # 返回加载的规则数量
        # Reload rule file (for hot reload)
        # Return number of loaded rules
        return self.load_rules()
