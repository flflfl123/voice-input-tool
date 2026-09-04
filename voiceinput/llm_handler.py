# -*- coding: utf-8 -*-
# LLM角色处理模块 - 当识别结果开头匹配角色名时，交由该角色处理
# 预置润色、小助理等角色，使用OpenAI兼容API调用LLM
# 参考自 CapsWriter-Offline 项目 (https://github.com/HaujetZhao/CapsWriter-Offline)
# CapsWriter-Offline 采用 MIT 协议开源，作者：HaujetZhao
# LLM role handler module - when recognition result starts with a role name, hand over to that role
# Pre-set roles like polish, assistant, etc., use OpenAI compatible API to call LLM
# Referenced from CapsWriter-Offline project's llm_handler.py

# 导入日志记录库
# Import logging library
import logging
# 导入路径处理库
# Import path processing library
from pathlib import Path
# 导入线程锁
# Import thread lock
from threading import Lock
# 导入 AST 模块用于安全解析角色文件（只允许字面量赋值，不执行任意代码）
# Import ast module for safe parsing of role files (only literal assignments allowed, no arbitrary code execution)
import ast

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 角色定义目录 ==========
# ========== Role definition directory ==========
ROLES_DIR = Path(__file__).parent.parent / "config" / "roles"


class LLMRole:
    # LLM角色定义类
    # 每个角色包含名称、触发词、系统提示词、输出模式、LLM参数等属性
    # LLM role definition class
    # Each role contains name, trigger words, system prompt, output mode, LLM params, etc.

    def __init__(self, name: str, trigger_words: list, system_prompt: str,
                 output_mode: str = "typing", enable_history: bool = True,
                 max_context: int = 10, temperature: float = None,
                 max_tokens: int = None, top_p: float = None):
        # 初始化LLM角色
        # name: 角色名称
        # trigger_words: 触发关键词列表
        # system_prompt: 系统提示词
        # output_mode: 输出模式（typing=打字输出，toast=弹窗输出，clipboard=剪贴板）
        # enable_history: 是否启用对话历史
        # max_context: 最大上下文轮数
        # temperature: LLM温度参数（None则使用默认值）
        # max_tokens: 最大生成token数（None则使用默认值）
        # top_p: top_p采样参数（None则使用默认值）
        # Initialize LLM role
        # name: role name
        # trigger_words: trigger keyword list
        # system_prompt: system prompt
        # output_mode: output mode (typing, toast, clipboard)
        # enable_history: whether to enable conversation history
        # max_context: max context rounds
        # temperature: LLM temperature param (None uses default)
        # max_tokens: max generation tokens (None uses default)
        # top_p: top_p sampling param (None uses default)

        # 保存角色名称
        # Save role name
        self.name = name
        # 保存触发关键词列表
        # Save trigger keyword list
        self.trigger_words = trigger_words
        # 保存系统提示词
        # Save system prompt
        self.system_prompt = system_prompt
        # 保存输出模式
        # Save output mode
        self.output_mode = output_mode
        # 保存是否启用对话历史
        # Save whether to enable conversation history
        self.enable_history = enable_history
        # 保存最大上下文轮数
        # Save max context rounds
        self.max_context = max_context
        # 保存LLM参数
        # Save LLM parameters
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        # 对话历史列表
        # Conversation history list
        self.history = []


class LLMHandler:
    # LLM角色处理器类
    # 管理所有角色定义，检测识别结果是否匹配角色，调用LLM处理
    # LLM role handler class
    # Manage all role definitions, detect if recognition result matches a role, call LLM to process

    def __init__(self, config: dict):
        # 初始化LLM处理器
        # config: 配置字典，包含LLM API信息
        # Initialize LLM handler
        # config: config dict, contains LLM API info

        # 保存配置引用
        # Save config reference
        self.config = config
        # 角色列表
        # Role list
        self._roles = []
        # 线程锁（保护 role.history 跨线程读写）
        # Thread lock (protect role.history cross-thread read/write)
        self._lock = Lock()
        # 加载角色定义
        # Load role definitions
        self._load_roles()
        # 记录初始化日志
        # Log initialization
        logger.info("LLM: 初始化完成，已加载 %d 个角色", len(self._roles))

    def _load_roles(self):
        # 从 config/roles/ 目录加载所有角色定义
        # 每个角色是一个 .py 文件，包含角色属性
        # Load all role definitions from config/roles/ directory
        # Each role is a .py file containing role attributes

        # 确保角色目录存在
        # Ensure role directory exists
        ROLES_DIR.mkdir(parents=True, exist_ok=True)

        # 添加内置默认角色
        # Add built-in default roles
        self._add_default_roles()

        # 遍历角色目录中的 .py 文件
        # Iterate .py files in role directory
        for role_file in ROLES_DIR.glob("*.py"):
            # 跳过以 _ 开头的文件
            # Skip files starting with _
            if role_file.name.startswith('_'):
                continue
            try:
                # 安全加载角色文件：用 AST 解析，只允许字面量赋值，不执行任何代码
                # Safe load role file: parse with AST, only literal assignments allowed, no code execution
                with open(role_file, "r", encoding="utf-8") as f:
                    source = f.read()
                # 解析为 AST 语法树
                # Parse into AST syntax tree
                tree = ast.parse(source, filename=str(role_file))
                role_dict = {}
                # 遍历顶层语句，只处理赋值语句
                # Iterate top-level statements, only process assignments
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        # 用 literal_eval 安全求值（只支持字面量：字符串/数字/列表/字典/布尔/None）
                        # literal_eval only supports literals: string/number/list/dict/bool/None
                        try:
                            value = ast.literal_eval(node.value)
                        except (ValueError, SyntaxError):
                            # 非字面量值（如函数调用、变量引用），跳过
                            # Non-literal value (e.g. function call, variable ref), skip
                            continue
                        # 将值赋给所有目标变量
                        # Assign value to all target variables
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                role_dict[target.id] = value
                # 提取角色属性
                # Extract role attributes
                name = role_dict.get('name', role_file.stem)
                trigger_words = role_dict.get('trigger_words', [name])
                system_prompt = role_dict.get('system_prompt', '')
                output_mode = role_dict.get('output_mode', 'typing')
                enable_history = role_dict.get('enable_history', True)
                max_context = role_dict.get('max_context', 10)
                # LLM参数（可选，None则使用默认值）
                # LLM parameters (optional, None uses default)
                temperature = role_dict.get('temperature', None)
                max_tokens = role_dict.get('max_tokens', None)
                top_p = role_dict.get('top_p', None)
                # 创建角色对象并添加到列表
                # Create role object and add to list
                role = LLMRole(
                    name=name,
                    trigger_words=trigger_words,
                    system_prompt=system_prompt,
                    output_mode=output_mode,
                    enable_history=enable_history,
                    max_context=max_context,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                )
                self._roles.append(role)
                logger.info("LLM: 加载角色 '%s' (触发词: %s)", name, trigger_words)
            except Exception as e:
                # 记录加载角色失败日志
                # Log role load failure
                logger.error("LLM: 加载角色文件失败 '%s': %s", role_file, e)

    def _add_default_roles(self):
        # 添加内置默认角色
        # Add built-in default roles

        # 润色角色：对文本进行润色优化
        # Polish role: polish and optimize text
        polish_role = LLMRole(
            name="润色",
            trigger_words=["润色", "修改", "优化"],
            system_prompt="你是一个文本润色助手。请对用户输入的文本进行润色，使其更加流畅、自然、专业。只输出润色后的文本，不要添加任何解释或前缀。",
            output_mode="typing",
            enable_history=False,
            max_context=1,
        )
        # 小助理角色：通用AI助手
        # Assistant role: general AI assistant
        assistant_role = LLMRole(
            name="小助理",
            trigger_words=["小助理", "助手"],
            system_prompt="你是一个智能小助理。请根据用户的输入提供帮助。直接输出回复内容，不要添加任何前缀。",
            output_mode="typing",
            enable_history=True,
            max_context=10,
        )
        # 翻译角色：将文本翻译为指定语言
        # Translation role: translate text to specified language
        translate_role = LLMRole(
            name="翻译",
            trigger_words=["翻译", "译"],
            system_prompt="你是一个翻译助手。请将用户输入的文本翻译为最合适的语言（如果用户指定了目标语言则翻译为该语言，否则自动判断）。只输出翻译结果，不要添加任何解释。",
            output_mode="typing",
            enable_history=False,
            max_context=1,
        )
        # 添加到角色列表
        # Add to role list
        self._roles.extend([polish_role, assistant_role, translate_role])

    def detect_role(self, text: str):
        # 检测文本是否匹配某个角色
        # text: 输入文本
        # 返回匹配的角色对象和去除触发词后的文本，未匹配返回None
        # Detect if text matches a role
        # text: input text
        # Return matched role object and text with trigger word removed, None if no match

        # 遍历所有角色
        # Iterate all roles
        for role in self._roles:
            # 遍历角色的触发词
            # Iterate role's trigger words
            for trigger in role.trigger_words:
                # 检查文本是否以触发词开头
                # Check if text starts with trigger word
                if text.startswith(trigger):
                    # 去除触发词和可能的标点
                    # Remove trigger word and possible punctuation
                    remaining = text[len(trigger):].strip()
                    # 去除触发词后面的逗号、句号等
                    # Remove comma, period etc. after trigger word
                    remaining = remaining.lstrip('，。、,.')
                    # 记录检测到角色日志
                    # Log detected role
                    logger.info("LLM: 检测到角色 '%s' (触发词: '%s')", role.name, trigger)
                    # 返回角色和剩余文本
                    # Return role and remaining text
                    return role, remaining
        # 未匹配任何角色，返回None
        # No role matched, return None
        return None

    def process(self, text: str, callback=None):
        # 处理文本：检测角色并调用LLM
        # text: 输入文本
        # callback: 结果回调函数，接收 (result_text, is_final) 参数
        # 返回True表示已由LLM处理，False表示未匹配角色
        # Process text: detect role and call LLM
        # text: input text
        # callback: result callback, receives (result_text, is_final) parameters
        # Return True if processed by LLM, False if no role matched

        # 检测角色
        # Detect role
        result = self.detect_role(text)
        # 如果未匹配角色，返回False
        # If no role matched, return False
        if result is None:
            return False

        # 解构角色和剩余文本
        # Destructure role and remaining text
        role, user_input = result
        # 如果去除触发词后没有剩余内容，返回False
        # If no remaining content after removing trigger word, return False
        if not user_input:
            logger.info("LLM: 触发词后无内容，跳过LLM处理")
            return False

        # 在新线程中调用LLM，避免阻塞
        # Call LLM in new thread to avoid blocking
        import threading
        threading.Thread(
            target=self._call_llm,
            args=(role, user_input, callback),
            daemon=True,
        ).start()
        # 返回True表示已由LLM处理
        # Return True meaning processed by LLM
        return True

    @staticmethod
    def _friendly_http_error(status_code: int) -> str:
        # 将 HTTP 状态码转换为用户友好的错误提示
        # 不暴露技术细节，只给出可操作的建议
        # Convert HTTP status code to user-friendly error message
        # No technical details, only actionable suggestions
        if status_code == 401:
            return "API 密钥错误，请检查配置"
        elif status_code == 403:
            return "API 密钥无权限，请检查账户"
        elif status_code == 404:
            return "API 地址错误或模型不存在"
        elif status_code == 429:
            return "请求过于频繁或余额不足"
        elif status_code >= 500:
            return "AI 服务器内部错误，请稍后重试"
        else:
            return f"请求失败（{status_code}）"

    @staticmethod
    def _friendly_exception_error(e: Exception) -> str:
        # 将异常对象转换为用户友好的错误提示
        # 根据异常类型给出可操作的建议
        # Convert exception to user-friendly error message
        # Give actionable suggestions based on exception type
        # 导入 httpx 异常类型（已在模块顶部导入 httpx）
        # Import httpx exception types (httpx already imported at module top)
        # 连接类异常：网络不通或服务器不可达
        # Connection errors: network down or server unreachable
        if isinstance(e, httpx.ConnectError):
            return "无法连接到 AI 服务器，请检查网络"
        # 连接超时：网络慢或服务器响应慢
        # Connection timeout: slow network or slow server
        elif isinstance(e, httpx.ConnectTimeout):
            return "连接 AI 服务器超时，请检查网络"
        # 读取超时：服务器响应太慢
        # Read timeout: server response too slow
        elif isinstance(e, httpx.ReadTimeout):
            return "AI 服务器响应超时，请稍后重试"
        # 其他 httpx 异常
        # Other httpx exceptions
        elif isinstance(e, httpx.HTTPError):
            return "网络请求异常，请检查网络和 API 配置"
        # 其他异常：给出通用提示，不暴露技术细节
        # Other exceptions: generic message, no technical details
        else:
            return "AI 处理异常，请检查配置"

    def _call_llm(self, role: LLMRole, user_input: str, callback=None):
        # 调用LLM API处理文本（支持流式输出）
        # role: 角色对象
        # user_input: 用户输入文本
        # callback: 结果回调函数，接收 (result_text, is_final) 参数
        # 流式输出时，is_final=False 表示中间结果，is_final=True 表示最终结果
        # Call LLM API to process text (supports streaming output)
        # role: role object
        # user_input: user input text
        # callback: result callback, receives (result_text, is_final)
        # For streaming, is_final=False means intermediate, is_final=True means final

        # 从配置获取LLM API信息
        # Get LLM API info from config
        base_url = self.config.get("llm_base_url", "").rstrip("/")
        api_key = self.config.get("llm_api_key", "")
        model = self.config.get("llm_model", "gpt-3.5-turbo")

        # 如果没有配置LLM API，使用ASR的API配置作为回退
        # If LLM API not configured, use ASR API config as fallback
        if not base_url:
            base_url = self.config.get("base_url", "").rstrip("/")
        if not api_key:
            api_key = self.config.get("api_key", "")

        # 检查API配置是否完整
        # Check if API config is complete
        if not base_url or not api_key:
            logger.warning("LLM: API未配置，无法调用LLM")
            if callback:
                callback("[LLM未配置]", True)
            return

        try:
            # 导入HTTP客户端
            # Import HTTP client
            import httpx
            # 构建API URL
            # Build API URL
            url = f"{base_url}/chat/completions"
            # 构建请求头
            # Build request headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            # 构建消息列表
            # Build message list
            # 如果开启去除语气词功能，在 system_prompt 后追加指令
            # If remove filler words enabled, append instruction to system_prompt
            system_prompt = role.system_prompt
            if self.config.get("llm_remove_filler", False):
                # 追加去除语气词指令：去除无意义口头语，保留有意义的指示词
                # Append filler removal instruction: remove meaningless fillers, keep meaningful words
                system_prompt = system_prompt + '\n\n额外要求：去除文本中的无意义语气词和口头语（如「呃」「啊」「嗯」「哦」「那个」「就是」「然后」等填充停顿的词语），但保留有实际意义的词汇（如「这个」「那个」用作指示代词时）。只去除填充停顿的无意义词语，保持原文语义和标点不变。'
            messages = [{"role": "system", "content": system_prompt}]
            # 如果启用历史，添加对话历史（加锁读取，防止与 clear_history 竞态）
            # If history enabled, add conversation history (lock protected, prevent race with clear_history)
            if role.enable_history and role.history:
                with self._lock:
                    messages.extend(list(role.history))
            # 添加用户输入
            # Add user input
            messages.append({"role": "user", "content": user_input})
            # 构建请求负载（启用流式输出）
            # Build request payload (enable streaming)
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            # 添加角色级别的LLM参数（如果角色定义了）
            # Add role-level LLM params (if defined in role)
            if role.temperature is not None:
                payload["temperature"] = role.temperature
            if role.max_tokens is not None:
                payload["max_tokens"] = role.max_tokens
            if role.top_p is not None:
                payload["top_p"] = role.top_p
            # 记录调用日志
            # Log call
            logger.info("LLM: 调用角色 '%s'（流式），输入: %s", role.name, user_input[:50])
            # 发送流式请求
            # 使用 with 管理 client，确保异常时也关闭连接池（修复资源泄漏）
            # Send streaming request
            # Use with to manage client, ensure connection pool closed on exception (fixes leak)
            with httpx.Client(timeout=60.0) as client:
                # 使用流式请求
                # Use streaming request
                with client.stream("POST", url, headers=headers, json=payload) as response:
                    # 检查响应状态
                    # Check response status
                    if response.status_code != 200:
                        # 读取错误信息
                        # Read error info
                        error_text = response.read().decode('utf-8', errors='replace')
                        logger.error("LLM: 请求失败: %d %s", response.status_code, error_text[:200])
                        if callback:
                            # 根据状态码给出用户友好的错误提示
                            # Give user-friendly error message based on status code
                            callback(f"[{LLMHandler._friendly_http_error(response.status_code)}]", True)
                        return
                    # 累积完整回复文本
                    # Accumulate full reply text
                    full_reply = ""
                    # 逐行读取SSE流
                    # Read SSE stream line by line
                    for line in response.iter_lines():
                        # 跳过空行
                        # Skip empty lines
                        if not line:
                            continue
                        # SSE格式：以 "data: " 开头
                        # SSE format: starts with "data: "
                        if line.startswith("data: "):
                            # 提取数据部分
                            # Extract data part
                            data = line[6:]
                            # 流结束标记
                            # Stream end marker
                            if data.strip() == "[DONE]":
                                break
                            try:
                                # 解析JSON数据
                                # Parse JSON data
                                import json
                                chunk = json.loads(data)
                                # 提取增量内容
                                # Extract delta content
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        # 累积回复
                                        # Accumulate reply
                                        full_reply += content
                                        # 调用回调传递中间结果
                                        # Call callback with intermediate result
                                        if callback:
                                            callback(full_reply, False)
                            except json.JSONDecodeError:
                                # JSON解析失败，跳过该行
                                # JSON parse failed, skip this line
                                continue
                # with client.stream 结束，response 已关闭（client 仍开，由外层 with 管理）
                # with client.stream ended, response closed (client still open, managed by outer with)
                # 记录成功日志
                # Log success
                logger.info("LLM: 角色 '%s' 回复完成: %s", role.name, full_reply[:50])
                # 如果启用历史，保存到历史（加锁保护，防止与 clear_history 竞态）
                # If history enabled, save to history (lock protected, prevent race with clear_history)
                if role.enable_history:
                    with self._lock:
                        role.history.append({"role": "user", "content": user_input})
                        role.history.append({"role": "assistant", "content": full_reply})
                        # 限制历史长度
                        # Limit history length
                        if len(role.history) > role.max_context * 2:
                            role.history = role.history[-role.max_context * 2:]
                # 调用回调传递最终结果
                # Call callback with final result
                if callback:
                    callback(full_reply, True)
        except Exception as e:
            # 记录异常日志（完整技术信息供调试）
            # Log exception (full technical info for debugging)
            logger.error("LLM: 调用异常: %s", e)
            if callback:
                # 给用户友好的错误提示（不暴露技术细节）
                # Give user-friendly error message (no technical details)
                callback(f"[{LLMHandler._friendly_exception_error(e)}]", True)

    def clear_history(self, role_name: str = None):
        # 清除角色的对话历史
        # role_name: 角色名称，为None时清除所有角色的历史
        # Clear conversation history for roles
        # role_name: role name, clear all roles' history when None
        # 加锁保护，防止与 _call_llm 中的 history 读写竞态
        # Lock protected, prevent race with history read/write in _call_llm
        with self._lock:
            if role_name:
                # 清除指定角色的历史
                # Clear specified role's history
                for role in self._roles:
                    if role.name == role_name:
                        role.history = []
                        logger.info("LLM: 已清除角色 '%s' 的对话历史", role_name)
                        return
                logger.warning("LLM: 未找到角色 '%s'", role_name)
            else:
                # 清除所有角色的历史
                # Clear all roles' history
                for role in self._roles:
                    role.history = []
                logger.info("LLM: 已清除所有角色的对话历史")

    def get_role_names(self) -> list:
        # 获取所有角色名称列表
        # Get list of all role names
        return [role.name for role in self._roles]
