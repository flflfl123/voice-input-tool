# -*- coding: utf-8 -*-
# 音频识别模块 - 从engine.py拆出，负责音频识别逻辑
# 包含OpenAI兼容格式和流式（豆包等）两种识别方式
# Audio Recognition Module - split from engine.py, handles audio recognition logic
# Contains OpenAI compatible format and streaming (Doubao etc.) recognition methods

# 导入异步操作支持库
# Import async operation support library
import asyncio
# 导入日志记录库
# Import logging library
import logging
# 导入Base64编码库（用于DashScope音频编码）
# Import Base64 library (for DashScope audio encoding)
import base64
# 导入HTTP客户端库（用于ASR识别请求）
# Import HTTP client library (for ASR recognition requests)
import httpx
# 导入音频文件处理库
# Import audio file processing library
import wave
# 导入内存字节流处理类
# Import memory byte stream processing class
from io import BytesIO

# 从asr_providers模块导入ASR提供商相关类
# Import ASR provider related classes from asr_providers module
from voiceinput.asr_providers import (
    ASRProvider,                        # ASR提供商抽象基类
                                        # ASR provider abstract base class
    DoubaoASRProvider,                  # 豆包大模型ASR提供商
                                        # Doubao large model ASR provider
    VolcengineASRProvider,              # 火山引擎ASR提供商
                                        # Volcano engine ASR provider
    OpenAICompatibleASRProvider,        # OpenAI兼容格式ASR提供商
                                        # OpenAI compatible format ASR provider
)

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


class AudioRecognizer:
    # 音频识别器类 - 负责将音频数据发送到ASR服务并获取识别结果
    # 支持OpenAI兼容格式和流式识别两种方式
    # Audio Recognizer class - sends audio data to ASR service and gets recognition results
    # Supports OpenAI compatible format and streaming recognition

    def __init__(self, config: dict, on_result_callback=None):
        # 初始化音频识别器
        # config: 配置字典，包含ASR提供商类型和认证信息等
        # on_result_callback: 识别结果回调函数，接收(text, is_final)参数
        # Initialize audio recognizer
        # config: configuration dictionary
        # on_result_callback: recognition result callback, receives (text, is_final)

        # 保存配置字典
        # Save configuration dictionary
        self.config = config
        # 保存结果回调函数
        # Save result callback function
        self._on_result_callback = on_result_callback
        # 初始化ASR提供商实例为空
        # Initialize ASR provider instance to None
        self.provider: ASRProvider = None

    def _create_provider(self) -> ASRProvider:
        # 根据配置创建ASR Provider实例
        # 返回对应的ASR提供商实例
        # Create ASR Provider instance based on configuration
        # Return corresponding ASR provider instance

        # 从配置中获取ASR提供商类型，默认为doubao
        # Get ASR provider type from config, default to doubao
        provider_type = self.config.get("asr_provider", "doubao")
        # 记录创建Provider的日志
        # Log creating Provider
        logger.info("识别: 创建ASR Provider实例 (类型: %s)", provider_type)

        # 判断是否为豆包大模型
        # Check if Doubao large model
        if provider_type == "doubao":
            # 记录豆包配置信息
            # Log Doubao configuration info
            logger.info("识别: 配置豆包ASR - Resource ID: %s, Mode: %s",
                       self.config.get("resource_id", ""), self.config.get("asr_mode", ""))
            # 创建豆包ASR提供商实例
            # Create Doubao ASR provider instance
            return DoubaoASRProvider(
                app_key=self.config.get("app_key", ""),             # 应用密钥 / Application key
                access_key=self.config.get("access_key", ""),       # 访问密钥 / Access key
                resource_id=self.config.get("resource_id", "volc.bigasr.sauc.duration"),  # 资源ID / Resource ID
                mode=self.config.get("asr_mode", "bigmodel_async"), # 识别模式 / Recognition mode
            )
        # 判断是否为火山引擎
        # Check if Volcano engine
        elif provider_type == "volcengine":
            # 记录火山引擎配置信息
            # Log Volcano engine configuration info
            logger.info("识别: 配置火山引擎ASR - Cluster: %s",
                       self.config.get("cluster", ""))
            # 创建火山引擎ASR提供商实例
            # Create Volcano engine ASR provider instance
            return VolcengineASRProvider(
                app_key=self.config.get("app_key", ""),             # 应用密钥 / Application key
                access_key=self.config.get("access_key", ""),       # 访问密钥 / Access key
                cluster=self.config.get("cluster", "volcengine_streaming_common"),  # 集群名称 / Cluster name
            )
        # 判断是否为OpenAI兼容格式
        # Check if OpenAI compatible format
        elif provider_type == "openai_compatible":
            # 记录OpenAI兼容配置信息
            # Log OpenAI compatible configuration info
            logger.info("识别: 配置OpenAI兼容ASR - Base URL: %s, Model: %s",
                       self.config.get("base_url", ""), self.config.get("model", ""))
            # 创建OpenAI兼容ASR提供商实例
            # Create OpenAI compatible ASR provider instance
            return OpenAICompatibleASRProvider(
                base_url=self.config.get("base_url", ""),           # API基础URL / API base URL
                api_key=self.config.get("api_key", ""),             # API密钥 / API key
                model=self.config.get("model", "whisper-1"),        # 模型名称 / Model name
            )
        else:
            # 不支持的ASR提供商类型，记录错误日志
            # Unsupported ASR provider type, log error
            logger.error("识别: 不支持的ASR提供商: %s", provider_type)
            # 抛出值错误异常
            # Raise ValueError exception
            raise ValueError(f"不支持的ASR提供商: {provider_type}")

    async def recognize(self, audio_chunks: list):
        # 识别所有音频块的主入口
        # audio_chunks: 录制的音频块列表
        # 根据ASR提供商类型选择不同的识别方式
        # Main entry for recognizing all audio chunks
        # audio_chunks: list of recorded audio chunks
        # Selects different recognition methods based on ASR provider type

        # 将所有音频块合并为一个完整的音频数据
        # Merge all audio chunks into complete audio data
        all_audio = b"".join(audio_chunks)
        # 记录合并音频日志
        # Log merged audio
        logger.info("识别: 合并音频，总长度 %d 字节", len(all_audio))

        # 从配置中获取ASR提供商类型
        # Get ASR provider type from config
        provider_type = self.config.get("asr_provider", "doubao")

        # 判断是否为OpenAI兼容格式
        # Check if OpenAI compatible format
        if provider_type == "openai_compatible":
            # OpenAI兼容格式：使用整个音频一次性识别
            # OpenAI compatible format: recognize entire audio at once
            await self._recognize_openai_compatible(all_audio)
        else:
            # 豆包等流式识别：分块发送
            # Streaming recognition (Doubao etc.): send in chunks
            await self._recognize_streaming(all_audio)

    async def _recognize_openai_compatible(self, audio_data: bytes):
        # 使用OpenAI兼容格式识别整个音频
        # audio_data: 完整的音频字节数据
        # Recognize entire audio using OpenAI compatible format
        # audio_data: complete audio byte data

        # 从配置中获取Base URL并去除末尾斜杠
        # Get Base URL from config and strip trailing slash
        base_url = self.config.get("base_url", "").rstrip("/")
        # 从配置中获取API密钥
        # Get API key from config
        api_key = self.config.get("api_key", "")
        # 从配置中获取模型名称
        # Get model name from config
        model = self.config.get("model", "whisper-1")
        # 判断是否为DashScope平台
        # Check if DashScope platform
        is_dashscope = "dashscope" in base_url.lower() if base_url else False

        # 创建内存字节流用于存储WAV文件
        # Create memory byte stream for WAV file
        wav_buffer = BytesIO()
        # 使用wave模块创建WAV文件
        # Create WAV file using wave module
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)                      # 设置单声道 / Set mono
            wf.setsampwidth(2)                      # 设置采样宽度为2字节（16位） / Set sample width 2 bytes (16-bit)
            wf.setframerate(16000)                  # 设置采样率为16000Hz / Set sample rate 16000Hz
            wf.writeframes(audio_data)              # 写入音频数据 / Write audio data
        # 将文件指针重置到开头
        # Reset file pointer to beginning
        wav_buffer.seek(0)

        # 初始化识别文本为空字符串
        # Initialize recognized text to empty string
        text = ""
        # 创建HTTP客户端，超时时间120秒
        # Create HTTP client, timeout 120 seconds
        client = httpx.Client(timeout=120.0)
        try:
            # 判断是否为DashScope平台
            # Check if DashScope platform
            if is_dashscope:
                # 百炼DashScope API - 使用base64编码音频
                # Bailian DashScope API - use base64 encoded audio
                # 读取WAV缓冲区的所有字节
                # Read all bytes from WAV buffer
                wav_bytes = wav_buffer.read()
                # 将字节数据编码为Base64字符串
                # Encode byte data to Base64 string
                b64_str = base64.b64encode(wav_bytes).decode("utf-8")
                # 构建Data URI格式
                # Build Data URI format
                data_uri = f"data:audio/wav;base64,{b64_str}"

                # 构建DashScope聊天补全API URL
                # Build DashScope chat completion API URL
                url = f"{base_url}/chat/completions"
                # 构建请求头
                # Build request headers
                headers = {
                    "Authorization": f"Bearer {api_key}",       # 认证令牌 / Auth token
                    "Content-Type": "application/json",         # 内容类型为JSON / Content type JSON
                }
                # 构建请求负载
                # Build request payload
                payload = {
                    "model": model,                             # 模型名称 / Model name
                    "messages": [
                        {
                            "role": "user",                     # 角色为用户 / Role user
                            "content": [
                                {
                                    "type": "input_audio",      # 内容类型为输入音频 / Content type input audio
                                    "input_audio": {
                                        "data": data_uri,       # 音频数据（Data URI格式） / Audio data (Data URI)
                                    },
                                }
                            ],
                        }
                    ],
                    "stream": False,                            # 不使用流式响应 / No streaming response
                }

                # 记录发送请求日志
                # Log sending request
                logger.info("识别: 发送DashScope识别请求，音频大小: %d 字节", len(wav_bytes))
                # 发送POST请求
                # Send POST request
                response = client.post(url, headers=headers, json=payload)
                # 检查响应状态码是否为200（成功）
                # Check if response status code is 200 (success)
                if response.status_code == 200:
                    # 解析JSON响应
                    # Parse JSON response
                    result = response.json()
                    # 获取choices列表
                    # Get choices list
                    choices = result.get("choices", [])
                    # 检查choices是否非空
                    # Check if choices is non-empty
                    if choices:
                        # 提取识别文本
                        # Extract recognized text
                        text = choices[0].get("message", {}).get("content", "")
                        # 记录识别成功日志
                        # Log recognition success
                        logger.info("识别: DashScope识别成功: %s", text[:50])
                    else:
                        # 记录返回空结果错误日志
                        # Log empty result error
                        logger.error("识别: DashScope返回空结果: %s", response.text[:200])
                else:
                    # 记录请求失败日志
                    # Log request failure
                    logger.error("识别: DashScope请求失败: %d %s", response.status_code, response.text[:200])
            else:
                # OpenAI标准API - 使用multipart/form-data上传音频
                # OpenAI standard API - use multipart/form-data to upload audio
                # 构建音频转录API URL
                # Build audio transcription API URL
                url = f"{base_url}/audio/transcriptions"
                # 构建请求头
                # Build request headers
                headers = {"Authorization": f"Bearer {api_key}"}
                # 构建表单文件数据
                # Build form file data
                files = {
                    "file": ("audio.wav", wav_buffer, "audio/wav"),     # 音频文件 / Audio file
                    "model": (None, model),                             # 模型名称 / Model name
                    "response_format": (None, "verbose_json"),          # 响应格式为详细JSON / Response format verbose JSON
                }
                # 记录发送请求日志
                # Log sending request
                logger.info("识别: 发送OpenAI ASR请求")
                # 发送POST请求（包含文件上传）
                # Send POST request (with file upload)
                response = client.post(url, headers=headers, files=files)
                # 检查响应状态码是否为200（成功）
                # Check if response status code is 200 (success)
                if response.status_code == 200:
                    # 解析JSON响应
                    # Parse JSON response
                    result = response.json()
                    # 提取识别文本
                    # Extract recognized text
                    text = result.get("text", "")
                    # 检查文本是否非空
                    # Check if text is non-empty
                    if text:
                        # 记录识别成功日志
                        # Log recognition success
                        logger.info("识别: OpenAI ASR识别成功: %s", text[:50])
                    else:
                        # 记录返回空结果错误日志
                        # Log empty result error
                        logger.error("识别: OpenAI ASR返回空结果")
                else:
                    # 记录请求失败日志
                    # Log request failure
                    logger.error("识别: OpenAI ASR请求失败: %d %s", response.status_code, response.text[:200])
        except Exception as e:
            # 记录识别异常日志
            # Log recognition exception
            logger.error("识别: 识别异常: %s", e)
        finally:
            # 无论成功或异常，都关闭HTTP客户端，防止连接泄漏
            # Always close HTTP client to prevent connection leak
            client.close()

        # 检查是否获取到文本且有结果回调函数
        # Check if text obtained and result callback exists
        if text and self._on_result_callback:
            # 调用结果回调函数，传递识别文本和最终结果标志
            # Call result callback with recognized text and final flag
            self._on_result_callback(text.strip(), is_final=True)
        # 检查是否没有识别到文本
        # Check if no text recognized
        elif not text:
            # 记录未识别到文字警告
            # Log no text recognized warning
            logger.warning("识别: 未识别到文字")
            # 检查结果回调函数是否存在
            # Check if result callback exists
            if self._on_result_callback:
                # 调用结果回调函数，传递空文本和最终结果标志
                # Call result callback with empty text and final flag
                self._on_result_callback("", is_final=True)

    async def _recognize_streaming(self, audio_data: bytes):
        # 使用流式识别（豆包等）
        # audio_data: 完整的音频字节数据
        # Streaming recognition (Doubao etc.)
        # audio_data: complete audio byte data

        # 创建ASR提供商实例
        # Create ASR provider instance
        self.provider = self._create_provider()
        # 连接到ASR服务
        # Connect to ASR service
        connected = await self.provider.connect()
        # 检查连接是否成功
        # Check if connection succeeded
        if not connected:
            # 记录连接失败日志
            # Log connection failure
            logger.error("识别: ASR连接失败")
            # 连接失败也要关闭provider，防止资源泄漏
            # Close provider even on connection failure to prevent resource leak
            await self.provider.close()
            # 返回
            # Return
            return

        # 设置分块大小为3200字节
        # Set chunk size to 3200 bytes
        chunk_size = 3200
        # 遍历音频数据，分块发送
        # Iterate audio data, send in chunks
        for i in range(0, len(audio_data), chunk_size):
            # 提取当前块数据
            # Extract current chunk data
            chunk = audio_data[i:i + chunk_size]
            # 发送音频块，标记不是最后一包
            # Send audio chunk, mark as not last
            await self.provider.send_audio(chunk, is_last=False)

        # 发送空数据标记最后一包，表示音频发送结束
        # Send empty data to mark last packet, indicating audio send complete
        await self.provider.send_audio(b"", is_last=True)

        # 等待2秒让服务端完成识别
        # Wait 2 seconds for server to complete recognition
        await asyncio.sleep(2.0)
        # 接收识别结果
        # Receive recognition result
        result = await self.provider.receive_result()
        # 检查结果是否存在且包含payload
        # Check if result exists and contains payload
        if result and "payload" in result:
            # 提取识别文本
            # Extract recognized text
            text = result.get("payload", {}).get("result", {}).get("text", "")
            # 检查文本是否非空且有结果回调函数
            # Check if text is non-empty and result callback exists
            if text and self._on_result_callback:
                # 调用结果回调函数，传递识别文本和最终结果标志
                # Call result callback with recognized text and final flag
                self._on_result_callback(text.strip(), is_final=True)
            # 检查是否没有识别到文本
            # Check if no text recognized
            elif not text:
                # 记录未识别到文字警告
                # Log no text recognized warning
                logger.warning("识别: 未识别到文字")

        # 关闭ASR连接
        # Close ASR connection
        await self.provider.close()
