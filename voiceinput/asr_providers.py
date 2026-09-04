# -*- coding: utf-8 -*-
# ASR Provider 抽象层和具体实现模块
# 支持三种语音识别服务：豆包大模型、火山引擎、OpenAI兼容格式
# ASR Provider abstraction layer and concrete implementation module
# Supports three speech recognition services: Doubao large model, Volcano engine, OpenAI compatible format

# 导入异步操作支持库
# Import async operation support library
import asyncio
# 导入数据压缩库
# Import data compression library
import gzip
# 导入JSON处理库
# Import JSON processing library
import json
# 导入日志记录库
# Import logging library
import logging
# 导入线程安全队列库
# Import thread-safe queue library
import queue
# 导入多线程支持库
# Import threading support library
import threading
# 导入时间处理库
# Import time processing library
import time
# 导入唯一标识符生成库
# Import unique identifier generation library
import uuid
# 导入音频文件处理库
# Import audio file processing library
import wave
# 导入抽象基类和抽象方法装饰器
# Import abstract base class and abstract method decorator
from abc import ABC, abstractmethod
# 导入内存字节流处理类
# Import memory byte stream processing class
from io import BytesIO

# 导入WebSocket客户端库
# Import WebSocket client library
import websockets

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# 定义语音识别通信协议版本号（二进制0001，即十进制1）
# Define speech recognition communication protocol version number (binary 0001, i.e. decimal 1)
PROTOCOL_VERSION = 0b0001

# ========== 消息类型常量定义 ==========
# ========== Message type constant definitions ==========
# 客户端发送完整请求（包含配置信息和音频数据）
# Client sends full request (includes config info and audio data)
CLIENT_FULL_REQUEST = 0b0001
# 客户端仅发送音频数据请求（不包含配置信息）
# Client sends audio data only request (no config info)
CLIENT_AUDIO_ONLY_REQUEST = 0b0010
# 服务端返回完整响应（包含识别结果）
# Server returns full response (includes recognition result)
SERVER_FULL_RESPONSE = 0b1001
# 服务端返回确认消息（ACK，表示收到请求）
# Server returns acknowledgment (ACK, indicates request received)
SERVER_ACK = 0b1011
# 服务端返回错误响应
# Server returns error response
SERVER_ERROR_RESPONSE = 0b1111

# ========== 序列标志常量定义 ==========
# ========== Sequence flag constant definitions ==========
# 不使用序列号
# Don't use sequence number
NO_SEQUENCE = 0b0000
# 使用正序列号（递增）
# Use positive sequence number (incrementing)
POS_SEQUENCE = 0b0001
# 使用负序列号（递减）
# Use negative sequence number (decrementing)
NEG_SEQUENCE = 0b0010

# ========== 数据序列化方式常量定义 ==========
# ========== Data serialization method constant definitions ==========
# 不进行序列化（原始二进制数据）
# No serialization (raw binary data)
NO_SERIALIZATION = 0b0000
# 使用JSON格式序列化
# Use JSON format serialization
JSON_SERIALIZATION = 0b0001

# ========== 数据压缩方式常量定义 ==========
# ========== Data compression method constant definitions ==========
# 不进行压缩
# No compression
NO_COMPRESSION = 0b0000
# 使用GZIP算法压缩
# Use GZIP algorithm compression
GZIP_COMPRESSION = 0b0001


def _generate_header(
    message_type=CLIENT_FULL_REQUEST,          # 消息类型（完整请求/音频请求等）
                                               # Message type (full request/audio request, etc.)
    message_type_specific_flags=NO_SEQUENCE,   # 消息类型特定标志（序列号类型）
                                               # Message type specific flag (sequence number type)
    serial_method=JSON_SERIALIZATION,          # 序列化方式（JSON/无）
                                               # Serialization method (JSON/none)
    compression_type=GZIP_COMPRESSION,         # 压缩方式（GZIP/无）
                                               # Compression method (GZIP/none)
    reserved_data=0x00,                        # 保留数据（备用字段）
                                               # Reserved data (backup field)
):
    # 生成协议头部字节数组
    # 创建空的可变字节数组
    # Generate protocol header byte array
    # Create empty mutable byte array
    header = bytearray()
    # 设置头部大小为1个字节
    # Set header size to 1 byte
    header_size = 1
    # 第一个字节：高4位是协议版本，低4位是头部大小
    # First byte: high 4 bits are protocol version, low 4 bits are header size
    header.append((PROTOCOL_VERSION << 4) | header_size)
    # 第二个字节：高4位是消息类型，低4位是消息类型特定标志
    # Second byte: high 4 bits are message type, low 4 bits are message type specific flag
    header.append((message_type << 4) | message_type_specific_flags)
    # 第三个字节：高4位是序列化方式，低4位是压缩方式
    # Third byte: high 4 bits are serialization method, low 4 bits are compression method
    header.append((serial_method << 4) | compression_type)
    # 第四个字节：保留数据
    # Fourth byte: reserved data
    header.append(reserved_data)
    # 返回构建好的头部字节数组
    # Return constructed header byte array
    return header


def _build_full_request(payload_dict: dict) -> bytes:
    # 构建完整请求数据包（包含头部和负载数据）
    # 调用头部生成函数，设置消息类型为完整请求
    # Build full request data packet (includes header and payload data)
    # Call header generation function, set message type to full request
    header = _generate_header(
        message_type=CLIENT_FULL_REQUEST,           # 设置为完整请求类型 / Set to full request type
        message_type_specific_flags=NO_SEQUENCE,    # 不使用序列号 / Don't use sequence number
        serial_method=JSON_SERIALIZATION,           # 使用JSON序列化 / Use JSON serialization
        compression_type=GZIP_COMPRESSION,          # 使用GZIP压缩 / Use GZIP compression
    )
    # 将字典转换为JSON字符串，再编码为字节，最后进行GZIP压缩
    # Convert dictionary to JSON string, encode to bytes, then GZIP compress
    payload_bytes = gzip.compress(json.dumps(payload_dict).encode("utf-8"))
    # 拼接：头部 + 负载长度（4字节大端序） + 压缩后的负载数据
    # Concatenate: header + payload length (4 bytes big-endian) + compressed payload data
    return header + len(payload_bytes).to_bytes(4, "big") + payload_bytes


def _build_audio_request(audio_data: bytes, is_last: bool = False) -> bytes:
    # 构建音频数据请求包
    # 调用头部生成函数，设置消息类型为仅音频请求
    # Build audio data request packet
    # Call header generation function, set message type to audio only request
    header = _generate_header(
        message_type=CLIENT_AUDIO_ONLY_REQUEST,     # 设置为音频请求类型 / Set to audio request type
        # 如果是最后一包使用负序列号，否则不使用序列号
        # If last packet use negative sequence number, otherwise don't use sequence number
        message_type_specific_flags=NEG_SEQUENCE if is_last else NO_SEQUENCE,
        serial_method=NO_SERIALIZATION,             # 音频数据不需要序列化 / Audio data doesn't need serialization
        compression_type=NO_COMPRESSION,            # 音频数据不压缩 / Audio data not compressed
    )
    # 拼接：头部 + 音频数据长度（4字节大端序） + 原始音频数据
    # Concatenate: header + audio data length (4 bytes big-endian) + raw audio data
    return header + len(audio_data).to_bytes(4, "big") + audio_data


def _parse_response(res: bytes) -> dict:
    # 解析服务端返回的响应数据
    # 从第一个字节提取头部大小（低4位）
    # Parse response data returned by server
    # Extract header size from first byte (low 4 bits)
    header_size = res[0] & 0x0f
    # 从第二个字节提取消息类型（高4位）
    # Extract message type from second byte (high 4 bits)
    message_type = res[1] >> 4
    # 从第三个字节提取压缩方式（低4位）
    # Extract compression method from third byte (low 4 bits)
    message_compression = res[2] & 0x0f
    # 从第三个字节提取序列化方式（高4位）
    # Extract serialization method from third byte (high 4 bits)
    serialization_method = res[2] >> 4

    # 根据头部大小计算负载数据的起始位置（头部大小 * 4）
    # Calculate payload data start position based on header size (header size * 4)
    payload = res[header_size * 4:]
    # 初始化结果字典
    # Initialize result dictionary
    result = {}
    # 初始化负载消息变量
    # Initialize payload message variable
    payload_msg = None

    # 判断消息类型，根据不同类型解析负载数据
    # Determine message type, parse payload data based on different types
    if message_type == SERVER_FULL_RESPONSE:
        # 完整响应类型：前4字节是负载大小
        # Full response type: first 4 bytes are payload size
        payload_size = int.from_bytes(payload[:4], "big", signed=True)
        # 提取负载消息内容
        # Extract payload message content
        payload_msg = payload[4:4 + payload_size]
    elif message_type == SERVER_ACK:
        # 确认消息类型：前4字节是序列号
        # Acknowledgment message type: first 4 bytes are sequence number
        seq = int.from_bytes(payload[:4], "big", signed=True)
        # 将序列号存入结果
        # Store sequence number in result
        result["seq"] = seq
        # 如果负载长度大于等于8字节，说明还有额外消息
        # If payload length >= 8 bytes, there are additional messages
        if len(payload) >= 8:
            # 第5-8字节是消息大小
            # Bytes 5-8 are message size
            payload_size = int.from_bytes(payload[4:8], "big", signed=False)
            # 提取消息内容
            # Extract message content
            payload_msg = payload[8:8 + payload_size]
        else:
            # 没有额外消息，直接返回结果
            # No additional messages, return result directly
            return result
    elif message_type == SERVER_ERROR_RESPONSE:
        # 错误响应类型：前4字节是错误码
        # Error response type: first 4 bytes are error code
        code = int.from_bytes(payload[:4], "big", signed=False)
        # 将错误码存入结果
        # Store error code in result
        result["code"] = code
        # 第5-8字节是消息大小
        # Bytes 5-8 are message size
        payload_size = int.from_bytes(payload[4:8], "big", signed=False)
        # 提取错误消息内容
        # Extract error message content
        payload_msg = payload[8:8 + payload_size]
    else:
        # 未知消息类型，直接返回空结果
        # Unknown message type, return empty result directly
        return result

    # 如果没有负载消息，直接返回结果
    # If no payload message, return result directly
    if payload_msg is None:
        return result

    # 根据压缩方式解压缩数据
    # Decompress data based on compression method
    if message_compression == GZIP_COMPRESSION:
        try:
            # 使用GZIP解压缩
            # Use GZIP decompression
            payload_msg = gzip.decompress(payload_msg)
        except Exception as e:
            # 解压缩失败时记录警告日志
            # Log warning when decompression fails
            logger.warning("解压缩失败 (%s)，尝试使用原始数据", e)

    # 根据序列化方式反序列化数据
    # Deserialize data based on serialization method
    if serialization_method == JSON_SERIALIZATION:
        try:
            # 将字节数据解码为UTF-8字符串，再解析为JSON对象
            # Decode byte data to UTF-8 string, then parse as JSON object
            result["payload"] = json.loads(payload_msg.decode("utf-8"))
        except Exception as e:
            # JSON解析失败时记录调试日志，并将payload置为None以避免后续处理出错
            # Record debug log when JSON parsing fails, set payload to None to avoid subsequent processing errors
            logger.debug("ASR: JSON解析异常: %s", e)
            result["payload"] = None
    else:
        # 不需要反序列化，直接存储原始字节数据
        # No deserialization needed, store raw byte data directly
        result["payload"] = payload_msg

    # 返回解析后的结果字典
    # Return parsed result dictionary
    return result


class ASRProvider(ABC):
    # ASR提供商抽象基类，定义所有语音识别服务必须实现的接口
    # ASR provider abstract base class, defines interface all speech recognition services must implement
    pass

    @abstractmethod
    async def connect(self) -> bool:
        # 连接到ASR语音识别服务
        # Connect to ASR speech recognition service
        # 返回True表示连接成功，False表示连接失败
        # Return True for successful connection, False for failed connection
        pass

    @abstractmethod
    async def send_audio(self, audio_data: bytes, is_last: bool = False):
        # 发送音频数据到识别服务
        # Send audio data to recognition service
        # audio_data: 音频字节数据
        # audio_data: audio byte data
        # is_last: 是否为最后一包音频数据
        # is_last: whether this is the last packet of audio data
        pass

    @abstractmethod
    async def receive_result(self) -> dict:
        # 接收识别结果
        # Receive recognition result
        # 返回包含识别结果的字典
        # Return dictionary containing recognition result
        pass

    @abstractmethod
    async def close(self):
        # 关闭与识别服务的连接
        # Close connection to recognition service
        pass

    @abstractmethod
    def get_name(self) -> str:
        # 获取提供商名称（用于界面显示）
        # Get provider name (for UI display)
        pass


class DoubaoASRProvider(ASRProvider):
    # 豆包大模型语音识别提供商实现类
    # Doubao large model speech recognition provider implementation class
    
    def __init__(self, app_key: str, access_key: str, resource_id: str,
                 mode: str = "bigmodel_async"):
        # 初始化豆包ASR提供商
        # Initialize Doubao ASR provider
        # app_key: 应用密钥
        # app_key: application key
        # access_key: 访问密钥
        # access_key: access key
        # resource_id: 资源ID
        # resource_id: resource ID
        # mode: 识别模式（bigmodel/bigmodel_nostream/bigmodel_async）
        # mode: recognition mode (bigmodel/bigmodel_nostream/bigmodel_async)
        
        # 保存应用密钥
        # Save application key
        self.app_key = app_key
        # 保存访问密钥
        # Save access key
        self.access_key = access_key
        # 保存资源ID
        # Save resource ID
        self.resource_id = resource_id
        # 保存识别模式
        # Save recognition mode
        self.mode = mode
        # 初始化WebSocket连接对象为空
        # Initialize WebSocket connection object to None
        self.ws = None
        # 生成唯一的连接标识符
        # Generate unique connection identifier
        self._connect_id = str(uuid.uuid4())

        # 定义识别模式与API路径的映射关系
        # Define mapping between recognition mode and API path
        mode_map = {
            "bigmodel": "/api/v3/sauc/bigmodel",              # 流式大模型模式 / Streaming large model mode
            "bigmodel_nostream": "/api/v3/sauc/bigmodel_nostream",  # 非流式大模型模式 / Non-streaming large model mode
            "bigmodel_async": "/api/v3/sauc/bigmodel_async",  # 异步大模型模式 / Async large model mode
        }
        # 根据模式构建完整的WebSocket URL
        # Build complete WebSocket URL based on mode
        self.uri = f"wss://openspeech.bytedance.com{mode_map.get(mode, mode_map['bigmodel_async'])}"

    def get_name(self) -> str:
        # 返回提供商名称
        # Return provider name
        return "豆包大模型语音识别"

    async def connect(self) -> bool:
        # 连接到豆包WebSocket服务
        # Connect to Doubao WebSocket service
        # 记录准备连接的日志
        # Log preparing to connect
        logger.info("豆包ASR: 准备连接 WebSocket: %s", self.uri)
        # 构建HTTP请求头，包含认证信息
        # Build HTTP request headers with authentication info
        headers = {
            "X-Api-App-Key": self.app_key,              # 应用密钥 / Application key
            "X-Api-Access-Key": self.access_key,        # 访问密钥 / Access key
            "X-Api-Resource-Id": self.resource_id,      # 资源ID / Resource ID
            "X-Api-Connect-Id": self._connect_id,       # 连接ID / Connection ID
        }
        # 记录请求头配置信息（只显示密钥前8位保护安全）
        # Log request header config info (only show first 8 chars of key for security)
        logger.info("豆包ASR: 请求头已配置 (App Key: %s..., Resource ID: %s)", 
                    self.app_key[:8] if self.app_key else "空", self.resource_id)
        try:
            # 记录正在建立连接
            # Log establishing connection
            logger.info("豆包ASR: 正在建立 WebSocket 连接...")
            # 建立WebSocket连接
            # Establish WebSocket connection
            self.ws = await websockets.connect(
                self.uri,                                   # 连接地址 / Connection URL
                additional_headers=headers,                 # 附加请求头 / Additional request headers
                max_size=None,                              # 不限制消息大小 / No message size limit
                ping_interval=None,                         # 不发送心跳 / No heartbeat
            )
            # 记录连接成功
            # Log connection success
            logger.info("豆包ASR: WebSocket连接成功")

            # 构建初始化请求参数
            # Build initialization request parameters
            req = {
                "user": {"uid": str(uuid.uuid4())},         # 用户唯一标识 / User unique identifier
                "audio": {
                    "format": "pcm",                        # 音频格式为PCM / Audio format PCM
                    "codec": "raw",                         # 编码方式为原始 / Encoding raw
                    "sample_rate": 16000,                   # 采样率16000Hz / Sample rate 16000Hz
                    "bits": 16,                             # 位深度16位 / Bit depth 16 bits
                    "channel": 1,                           # 单声道 / Mono channel
                },
                "request": {
                    "reqid": str(uuid.uuid4()),             # 请求唯一标识 / Request unique identifier
                    "sequence": 1,                          # 序列号为1 / Sequence number 1
                    "nbest": 1,                             # 返回最佳结果 / Return best result
                    "show_utterances": True,                # 显示话语信息 / Show utterance info
                },
            }
            # 记录准备发送初始化请求
            # Log preparing to send initialization request
            logger.info("豆包ASR: 准备发送初始化请求")
            # 调用函数构建完整请求数据包
            # Call function to build full request data packet
            data = _build_full_request(req)
            # 记录请求数据包大小
            # Log request data packet size
            logger.info("豆包ASR: 初始化请求已构建 (%d bytes)", len(data))
            # 通过WebSocket发送数据
            # Send data via WebSocket
            await self.ws.send(data)
            # 记录请求已发送
            # Log request sent
            logger.info("豆包ASR: 初始化请求已发送")
            # 记录连接初始化完成
            # Log connection initialization complete
            logger.info("豆包ASR: 连接初始化完成")
            # 返回连接成功
            # Return connection success
            return True
        except Exception as e:
            # 捕获异常并记录错误日志
            # Catch exception and log error
            logger.error("豆包ASR连接失败: %s", e)
            # 返回连接失败
            return False

    async def send_audio(self, audio_data: bytes, is_last: bool = False):
        # 发送音频数据到豆包服务
        # Send audio data to Doubao service
        # 检查WebSocket连接是否存在
        # Check if WebSocket connection exists
        if self.ws:
            try:
                # 构建音频数据请求包
                # Build audio data request packet
                data = _build_audio_request(audio_data, is_last)
                # 通过WebSocket发送音频数据
                # Send audio data via WebSocket
                await self.ws.send(data)
                # 如果是最后一包，记录日志
                # If last packet, log message
                if is_last:
                    logger.info("豆包ASR: 已发送最后一包音频数据 (%d bytes)", len(audio_data))
            except websockets.exceptions.ConnectionClosed:
                # 连接已关闭时记录警告
                # Log warning when connection closed
                logger.warning("豆包ASR: 发送音频时连接已关闭")
            except Exception as e:
                # 其他异常记录错误
                # Log error for other exceptions
                logger.error("豆包ASR: 发送音频异常: %s", e)

    async def receive_result(self) -> dict:
        # 接收豆包识别结果
        # Receive Doubao recognition result
        # 检查WebSocket连接是否存在
        # Check if WebSocket connection exists
        if self.ws:
            try:
                # 等待接收数据，超时时间1秒
                # Wait to receive data, timeout 1 second
                res = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                # 如果收到的是字节数据
                # If received byte data
                if isinstance(res, bytes):
                    # 调用解析函数解析响应
                    # Call parse function to parse response
                    parsed = _parse_response(res)
                    # 记录调试日志（只显示前200字符）
                    # Log debug message (only show first 200 chars)
                    logger.debug("豆包ASR收到响应: %s", str(parsed)[:200])
                    # 返回解析结果
                    # Return parsed result
                    return parsed
            except asyncio.TimeoutError:
                # 超时返回空字典
                # Return empty dict on timeout
                return {}
            except websockets.exceptions.ConnectionClosed:
                # 连接关闭返回错误信息
                # Return error message on connection closed
                return {"error": "connection_closed"}
            except Exception as e:
                # 其他异常记录错误并返回错误信息
                # Log error and return error message for other exceptions
                logger.error("豆包ASR: 接收结果异常: %s", e)
                return {"error": str(e)}
        # 连接不存在时返回空字典
        # Return empty dict when connection doesn't exist
        return {}

    async def close(self):
        # 关闭豆包连接
        # Close Doubao connection
        # 检查WebSocket连接是否存在
        # Check if WebSocket connection exists
        if self.ws:
            try:
                # 关闭WebSocket连接
                # Close WebSocket connection
                await self.ws.close()
            except Exception as e:
                # 关闭豆包WebSocket连接失败时记录调试日志，连接清理异常不影响程序退出
                # Record debug log when closing Doubao WebSocket connection fails, cleanup exception doesn't affect program exit
                logger.debug("豆包ASR: 关闭连接异常: %s", e)
            # 将连接对象置为空
            # Set connection object to None
            self.ws = None


class VolcengineASRProvider(ASRProvider):
    # 火山引擎流式语音识别提供商实现类
    # Volcengine streaming speech recognition provider implementation class
    
    def __init__(self, app_key: str, access_key: str,
                 cluster: str = "volcengine_streaming_common"):
        # 初始化火山引擎ASR提供商
        # Initialize Volcengine ASR provider
        # app_key: 应用密钥
        # app_key: application key
        # access_key: 访问密钥
        # access_key: access key
        # cluster: 集群名称
        # cluster: cluster name
        
        # 保存应用密钥
        # Save application key
        self.app_key = app_key
        # 保存访问密钥
        # Save access key
        self.access_key = access_key
        # 保存集群名称
        # Save cluster name
        self.cluster = cluster
        # 初始化WebSocket连接对象为空
        # Initialize WebSocket connection object to None
        self.ws = None
        # 生成唯一的连接标识符
        # Generate unique connection identifier
        self._connect_id = str(uuid.uuid4())
        # 设置火山引擎WebSocket地址
        # Set Volcengine WebSocket URL
        self.uri = "wss://openspeech.bytedance.com/api/v2/asr"

    def get_name(self) -> str:
        # 返回提供商名称
        # Return provider name
        return "火山引擎流式语音识别"

    def _build_volcengine_full_request(self, reqid: str) -> bytes:
        # 构建火山引擎完整请求数据包
        # Build Volcengine full request data packet
        # reqid: 请求唯一标识符
        # reqid: request unique identifier
        
        # 构建请求参数
        # Build request parameters
        req = {
            "app": {
                "appid": self.app_key,                      # 应用ID / Application ID
                "cluster": self.cluster,                    # 集群名称 / Cluster name
                "token": self.access_key,                   # 访问令牌 / Access token
            },
            "user": {"uid": str(uuid.uuid4())},             # 用户唯一标识 / User unique identifier
            "request": {
                "reqid": reqid,                             # 请求ID / Request ID
                "nbest": 1,                                 # 返回最佳结果 / Return best result
                # 处理工作流：音频输入->重采样->分割->VAD->特征提取->解码->ITN->NLU标点
                # Processing workflow: audio_in->resample->partition->vad->fe->decode->itn->nlu_punctuate
                "workflow": "audio_in,resample,partition,vad,fe,decode,itn,nlu_punctuate",
                "show_language": False,                     # 不显示语言信息 / Don't show language info
                "show_utterances": True,                    # 显示话语信息 / Show utterance info
                "result_type": "full",                      # 返回完整结果 / Return full result
                "sequence": 1,                              # 序列号为1 / Sequence number 1
            },
            "audio": {
                "format": "pcm",                            # 音频格式为PCM / Audio format PCM
                "rate": 16000,                              # 采样率16000Hz / Sample rate 16000Hz
                "language": "zh-CN",                        # 语言为中文 / Language Chinese
                "bits": 16,                                 # 位深度16位 / Bit depth 16 bits
                "channel": 1,                               # 单声道 / Mono channel
                "codec": "raw",                             # 编码方式为原始 / Encoding raw
            },
        }
        # 将请求参数转换为JSON并压缩
        # Convert request parameters to JSON and compress
        payload_bytes = gzip.compress(json.dumps(req).encode("utf-8"))
        # 生成协议头部
        # Generate protocol header
        header = _generate_header(
            message_type=CLIENT_FULL_REQUEST,               # 完整请求类型 / Full request type
            message_type_specific_flags=NO_SEQUENCE,        # 不使用序列号 / Don't use sequence number
            serial_method=JSON_SERIALIZATION,               # JSON序列化 / JSON serialization
            compression_type=GZIP_COMPRESSION,              # GZIP压缩 / GZIP compression
        )
        # 拼接：头部 + 负载长度 + 压缩负载数据
        # Concatenate: header + payload length + compressed payload data
        return header + len(payload_bytes).to_bytes(4, "big") + payload_bytes

    def _build_volcengine_audio_request(self, audio_data: bytes, is_last: bool = False) -> bytes:
        # 构建火山引擎音频数据请求包
        # Build Volcengine audio data request packet
        # audio_data: 音频字节数据
        # audio_data: audio byte data
        # is_last: 是否为最后一包
        # is_last: whether this is the last packet
        
        # 对音频数据进行GZIP压缩
        # Compress audio data with GZIP
        compressed = gzip.compress(audio_data)
        # 生成协议头部
        # Generate protocol header
        header = _generate_header(
            message_type=CLIENT_AUDIO_ONLY_REQUEST,         # 音频请求类型 / Audio request type
            # 最后一包使用负序列号，否则不使用序列号
            # Use negative sequence number for last packet, otherwise don't use sequence number
            message_type_specific_flags=NEG_SEQUENCE if is_last else NO_SEQUENCE,
            serial_method=NO_SERIALIZATION,                 # 不需要序列化 / No serialization needed
            compression_type=GZIP_COMPRESSION,              # GZIP压缩 / GZIP compression
        )
        # 拼接：头部 + 压缩数据长度 + 压缩数据
        # Concatenate: header + compressed data length + compressed data
        return header + len(compressed).to_bytes(4, "big") + compressed

    async def connect(self) -> bool:
        # 连接到火山引擎WebSocket服务
        # Connect to Volcengine WebSocket service
        # 记录连接地址
        # Log connection URL
        logger.info("火山引擎ASR: 连接 %s", self.uri)
        # 记录认证信息（只显示密钥前8位）
        # Log authentication info (only show first 8 chars of key)
        logger.info("火山引擎ASR: App Key=%s..., Cluster=%s", 
                    self.app_key[:8] if self.app_key else "空", self.cluster)
        
        # 构建带访问令牌的URL
        # Build URL with access token
        uri_with_token = f"{self.uri}?access_token={self.access_key}"
        try:
            # 建立WebSocket连接
            # Establish WebSocket connection
            self.ws = await websockets.connect(uri_with_token, max_size=None, ping_interval=None)
            # 记录连接成功
            # Log connection success
            logger.info("火山引擎ASR: WebSocket 已连接")

            # 生成请求ID
            # Generate request ID
            reqid = str(uuid.uuid4())
            # 构建完整请求数据包
            # Build full request data packet
            data = self._build_volcengine_full_request(reqid)
            # 发送初始化请求
            # Send initialization request
            await self.ws.send(data)
            # 记录请求已发送
            # Log request sent
            logger.info("火山引擎ASR: 初始化请求已发送 (%d bytes)", len(data))

            # 等待服务端响应，超时时间5秒
            # Wait for server response, timeout 5 seconds
            res = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            # 解析响应数据
            # Parse response data
            result = _parse_response(res)
            
            # 获取顶层错误码
            # Get top-level error code
            top_code = result.get("code", 0)
            # 如果顶层错误码不为0，表示连接失败
            # If top-level error code is not 0, connection failed
            if top_code != 0:
                # 获取错误消息
                # Get error message
                message = result.get("payload", {}).get("message", "未知错误")
                # 记录错误日志
                # Log error
                logger.error("火山引擎ASR: 错误 %d - %s", top_code, message)
                # 返回连接失败
                # Return connection failed
                return False
            
            # 检查是否有负载消息
            # Check if there is payload message
            if "payload_msg" in result:
                # 获取负载消息
                # Get payload message
                payload_msg = result["payload_msg"]
                # 获取消息中的状态码
                # Get status code from message
                code = payload_msg.get("code", 0)
                # 如果状态码不为1000，表示初始化失败
                # If status code is not 1000, initialization failed
                if code != 1000:
                    # 记录失败日志
                    # Log failure
                    logger.error("火山引擎ASR: 初始化失败 %s", payload_msg)
                    # 返回连接失败
                    # Return connection failed
                    return False
                # 记录初始化成功
                # Log initialization success
                logger.info("火山引擎ASR: 初始化成功")
            else:
                # 没有负载消息，记录收到ACK
                # No payload message, log received ACK
                logger.info("火山引擎ASR: 收到 ACK (seq=%d)", result.get("seq", 0))
            
            # 返回连接成功
            # Return connection success
            return True
        except asyncio.TimeoutError:
            # 超时记录错误日志
            # Log timeout error
            logger.error("火山引擎ASR: 响应超时")
            # 返回连接失败
            # Return connection failed
            return False
        except Exception as e:
            # 其他异常记录错误日志
            # Log error for other exceptions
            logger.error("火山引擎ASR: 连接失败: %s", e)
            # 返回连接失败
            # Return connection failed
            return False

    async def send_audio(self, audio_data: bytes, is_last: bool = False):
        # 发送音频数据到火山引擎服务
        # Send audio data to Volcengine service
        # 检查WebSocket连接是否存在
        # Check if WebSocket connection exists
        if self.ws:
            try:
                # 构建音频数据请求包
                # Build audio data request packet
                data = self._build_volcengine_audio_request(audio_data, is_last)
                # 通过WebSocket发送数据
                # Send data via WebSocket
                await self.ws.send(data)
                # 如果是最后一包，记录日志
                # If last packet, log message
                if is_last:
                    logger.info("火山引擎ASR: 已发送最后一包音频数据 (%d bytes)", len(audio_data))
            except websockets.exceptions.ConnectionClosed:
                # 连接已关闭时记录警告
                # Log warning when connection closed
                logger.warning("火山引擎ASR: 发送音频时连接已关闭")
            except Exception as e:
                # 其他异常记录错误
                # Log error for other exceptions
                logger.error("火山引擎ASR: 发送音频异常: %s", e)

    async def receive_result(self) -> dict:
        # 接收火山引擎识别结果
        # Receive Volcengine recognition result
        # 检查WebSocket连接是否存在
        # Check if WebSocket connection exists
        if self.ws:
            try:
                # 等待接收数据，超时时间1秒
                # Wait to receive data, timeout 1 second
                res = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                # 如果收到的是字节数据
                # If received byte data
                if isinstance(res, bytes):
                    # 调用解析函数解析响应
                    # Call parse function to parse response
                    parsed = _parse_response(res)
                    # 提取消息类型
                    # Extract message type
                    msg_type = res[1] >> 4
                    # 记录响应信息
                    # Log response info
                    logger.info("火山引擎ASR: 收到响应: type=%d, parsed=%s", msg_type, str(parsed)[:300])
                    # 返回解析结果
                    # Return parsed result
                    return parsed
            except asyncio.TimeoutError:
                # 超时返回空字典
                # Return empty dict on timeout
                return {}
            except websockets.exceptions.ConnectionClosed:
                # 连接关闭返回错误信息
                # Return error message on connection closed
                return {"error": "connection_closed"}
            except Exception as e:
                # 其他异常记录错误并返回错误信息
                # Log error and return error message for other exceptions
                logger.error("火山引擎ASR: 接收结果异常: %s", e)
                return {"error": str(e)}
        # 连接不存在时返回空字典
        # Return empty dict when connection doesn't exist
        return {}

    async def close(self):
        # 关闭火山引擎连接
        # Close Volcengine connection
        # 检查WebSocket连接是否存在
        # Check if WebSocket connection exists
        if self.ws:
            try:
                # 关闭WebSocket连接
                # Close WebSocket connection
                await self.ws.close()
            except Exception as e:
                # 关闭火山引擎WebSocket连接失败时记录调试日志，连接清理异常不影响程序退出
                # Record debug log when closing Volcengine WebSocket connection fails, cleanup exception doesn't affect program exit
                logger.debug("火山引擎ASR: 关闭连接异常: %s", e)
            # 将连接对象置为空
            # Set connection object to None
            self.ws = None


class OpenAICompatibleASRProvider(ASRProvider):
    # OpenAI兼容格式语音识别提供商实现类
    # OpenAI compatible format speech recognition provider implementation class
    # 支持OpenAI标准API和DashScope（百炼）平台
    # Supports OpenAI standard API and DashScope platform
    
    def __init__(self, base_url: str, api_key: str, model: str = "whisper-1"):
        # 初始化OpenAI兼容ASR提供商
        # Initialize OpenAI compatible ASR provider
        # base_url: API基础URL
        # base_url: API base URL
        # api_key: API密钥
        # api_key: API key
        # model: 模型名称（默认whisper-1）
        # model: model name (default whisper-1)
        
        # 去除base_url末尾的斜杠（如果存在）
        # Remove trailing slash from base_url (if exists)
        self.base_url = base_url.rstrip("/") if base_url else ""
        # 保存API密钥
        # Save API key
        self.api_key = api_key
        # 保存模型名称
        # Save model name
        self.model = model
        # 创建音频队列，最大容量200
        # Create audio queue, max capacity 200
        self._audio_queue = queue.Queue(maxsize=200)
        # 设置音频采样率为16000Hz
        # Set audio sample rate to 16000Hz
        self._sample_rate = 16000
        # 初始化运行状态为False
        # Initialize running state to False
        self._running = False
        # 创建结果队列
        # Create result queue
        self._result_queue = queue.Queue()
        # 初始化处理线程为空
        # Initialize processing thread to None
        self._thread = None
        # 判断是否为DashScope平台（URL中包含dashscope）
        # Check if DashScope platform (URL contains dashscope)
        self._is_dashscope = "dashscope" in base_url.lower() if base_url else False
        # 初始化百炼平台标志为False
        # Initialize Bailian platform flag to False
        self._is_bailian = False
        # 如果没有配置base_url但有api_key，自动配置为百炼平台
        # If base_url not configured but api_key exists, auto-configure as Bailian platform
        if not self.base_url and self.api_key:
            # 设置百炼平台标志为True
            # Set Bailian platform flag to True
            self._is_bailian = True
            # 设置默认Base URL为百炼平台地址
            # Set default Base URL to Bailian platform address
            self.base_url = "https://dashscope.aliyuncs.com/compatible-mode"
            # 记录自动配置日志
            # Log auto-configuration
            logger.info("检测到百炼平台配置，使用默认 Base URL: %s", self.base_url)

    def get_name(self) -> str:
        # 返回提供商名称
        # Return provider name
        # 如果是DashScope平台
        # If DashScope platform
        if self._is_dashscope:
            return "DashScope语音识别 (千问ASR)"
        # 否则返回通用名称
        # Otherwise return generic name
        return "OpenAI兼容格式语音识别"

    async def connect(self) -> bool:
        # 初始化OpenAI兼容ASR
        # Initialize OpenAI compatible ASR
        # 记录初始化配置检查
        # Log initialization config check
        logger.info("OpenAI兼容ASR: 初始化配置检查")
        # 检查base_url和api_key是否都已配置
        # Check if base_url and api_key are both configured
        if not self.base_url or not self.api_key:
            # 记录配置缺失错误日志
            # Log missing config error
            logger.error("OpenAI兼容ASR: base_url或api_key未配置 (base_url='%s', api_key='%s')", 
                        self.base_url, "已配置" if self.api_key else "未配置")
            # 返回初始化失败
            # Return initialization failed
            return False
        # 记录配置完成信息
        # Log config completion
        logger.info("OpenAI兼容ASR: 配置完成 - Base URL: %s, Model: %s, DashScope: %s, 百炼: %s", 
                    self.base_url, self.model, self._is_dashscope, self._is_bailian)
        # 设置运行状态为True
        # Set running state to True
        self._running = True
        # 重新创建音频队列
        # Recreate audio queue
        self._audio_queue = queue.Queue(maxsize=200)
        # 创建处理线程，目标函数为_process_loop
        # Create processing thread, target function is _process_loop
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        # 记录启动处理线程日志
        # Log start processing thread
        logger.info("OpenAI兼容ASR: 启动处理线程")
        # 启动线程
        # Start thread
        self._thread.start()
        # 记录启动成功日志
        # Log start success
        logger.info("OpenAI兼容ASR: 已启动 (model=%s)", self.model)
        # 返回初始化成功
        # Return initialization success
        return True

    def _process_loop(self):
        # 音频处理循环 - 累积音频并发送识别请求
        # Audio processing loop - accumulate audio and send recognition requests
        # 此函数在独立线程中运行
        # This function runs in a separate thread
        
        # 导入HTTP客户端库
        # Import HTTP client library
        import httpx
        # 导入Base64编码库
        # Import Base64 encoding library
        import base64

        # 创建HTTP客户端，超时时间60秒
        # Create HTTP client, timeout 60 seconds
        client = httpx.Client(timeout=60.0)
        # 创建音频缓冲区（可变字节数组）
        # Create audio buffer (mutable byte array)
        audio_buffer = bytearray()
        # 初始化处理的音频块计数器
        # Initialize processed audio chunk counter
        total_chunks = 0

        # 主循环：当运行状态为True时持续运行
        # Main loop: continue running when running state is True
        while self._running:
            try:
                try:
                    # 尝试从音频队列非阻塞获取数据
                    # Try to get data from audio queue non-blocking
                    chunk = self._audio_queue.get_nowait()
                    # 将音频块追加到缓冲区
                    # Append audio chunk to buffer
                    audio_buffer.extend(chunk)
                    # 增加处理块计数
                    # Increment processed chunk count
                    total_chunks += 1
                except queue.Empty:
                    # 队列为空时等待50毫秒
                    # Wait 50ms when queue is empty
                    time.sleep(0.05)
                    # 继续下一次循环
                    # Continue to next iteration
                    continue

                # 检查缓冲区是否累积了足够的数据（32000字节 = 1秒音频）
                # Check if buffer has accumulated enough data (32000 bytes = 1 second audio)
                if len(audio_buffer) < 32000:
                    # 数据不够，继续累积
                    # Not enough data, continue accumulating
                    continue

                # 记录发送识别请求日志
                # Log sending recognition request
                logger.info("OpenAI兼容ASR: 累积 %d 字节，发送识别请求", len(audio_buffer))
                # 将缓冲区数据转换为不可变字节
                # Convert buffer data to immutable bytes
                audio_data = bytes(audio_buffer)
                # 清空缓冲区
                # Clear buffer
                audio_buffer = bytearray()

                # 创建内存字节流用于存储WAV文件
                # Create in-memory byte stream to store WAV file
                wav_buffer = BytesIO()
                # 使用wave模块创建WAV文件
                # Use wave module to create WAV file
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(1)                      # 设置单声道 / Set mono channel
                    wf.setsampwidth(2)                      # 设置采样宽度为2字节（16位） / Set sample width to 2 bytes (16 bits)
                    wf.setframerate(self._sample_rate)      # 设置采样率 / Set sample rate
                    wf.writeframes(audio_data)              # 写入音频数据 / Write audio data
                # 将文件指针重置到开头
                # Reset file pointer to beginning
                wav_buffer.seek(0)

                # 根据平台类型调用不同的API
                # Call different API based on platform type
                if self._is_dashscope:
                    # 调用DashScope API进行识别
                    # Call DashScope API for recognition
                    text = self._call_dashscope(client, wav_buffer, base64)
                else:
                    # 调用OpenAI标准API进行识别
                    # Call OpenAI standard API for recognition
                    text = self._call_openai(client, wav_buffer)

                # 检查是否获取到识别结果
                # Check if recognition result obtained
                if text:
                    # 记录识别结果（只显示前50字符）
                    # Log recognition result (only show first 50 chars)
                    logger.info("OpenAI兼容ASR: 识别结果: %s", text[:50])
                    # 将结果放入结果队列
                    # Put result into result queue
                    self._result_queue.put({
                        "payload": {
                            "result": {
                                "text": text,               # 识别文本 / Recognition text
                                "is_final": True,           # 标记为最终结果 / Mark as final result
                            }
                        }
                    })
                else:
                    # 记录未获取到结果的警告
                    # Log warning for not getting result
                    logger.warning("OpenAI兼容ASR: 未获取到识别结果")

            except Exception as e:
                # 捕获异常并记录错误日志
                # Catch exception and log error
                logger.error("ASR处理异常: %s", e)
                # 等待500毫秒后继续
                # Wait 500ms then continue
                time.sleep(0.5)

        # 停止时处理剩余的音频数据
        # Process remaining audio data when stopping
        if len(audio_buffer) > 0:
            # 记录处理剩余音频日志
            # Log processing remaining audio
            logger.info("OpenAI兼容ASR: 停止时处理剩余 %d 字节音频", len(audio_buffer))
            try:
                # 创建内存字节流
                # Create in-memory byte stream
                wav_buffer = BytesIO()
                # 创建WAV文件
                # Create WAV file
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(1)                      # 单声道 / Mono
                    wf.setsampwidth(2)                      # 16位 / 16 bits
                    wf.setframerate(self._sample_rate)      # 采样率 / Sample rate
                    wf.writeframes(bytes(audio_buffer))     # 写入剩余音频 / Write remaining audio
                # 重置文件指针
                # Reset file pointer
                wav_buffer.seek(0)

                # 根据平台调用不同API
                # Call different API based on platform
                if self._is_dashscope:
                    text = self._call_dashscope(client, wav_buffer, base64)
                else:
                    text = self._call_openai(client, wav_buffer)

                # 检查是否获取到识别结果
                # Check if recognition result obtained
                if text:
                    # 记录剩余音频识别结果
                    # Log remaining audio recognition result
                    logger.info("OpenAI兼容ASR: 剩余音频识别结果: %s", text[:50])
                    # 将结果放入结果队列
                    # Put result into result queue
                    self._result_queue.put({
                        "payload": {
                            "result": {
                                "text": text,
                                "is_final": True,
                            }
                        }
                    })
            except Exception as e:
                # 记录剩余音频识别失败日志
                # Log remaining audio recognition failure
                logger.error("OpenAI兼容ASR: 剩余音频识别失败: %s", e)

        # 记录处理线程结束日志
        # Log processing thread end
        logger.info("OpenAI兼容ASR: 处理线程结束，共处理 %d 个块", total_chunks)
        # 关闭HTTP客户端
        # Close HTTP client
        client.close()

    def _call_dashscope(self, client, wav_buffer, base64_mod) -> str:
        # 调用DashScope API进行语音识别
        # Call DashScope API for speech recognition
        # client: HTTP客户端
        # client: HTTP client
        # wav_buffer: WAV音频数据缓冲区
        # wav_buffer: WAV audio data buffer
        # base64_mod: base64模块
        # base64_mod: base64 module
        
        # 导入base64模块
        # Import base64 module
        import base64

        # 读取WAV缓冲区的所有字节
        # Read all bytes from WAV buffer
        wav_bytes = wav_buffer.read()
        # 将字节数据编码为Base64字符串
        # Encode byte data to Base64 string
        b64_str = base64.b64encode(wav_bytes).decode("utf-8")
        # 构建Data URI格式（包含MIME类型和Base64数据）
        # Build Data URI format (includes MIME type and Base64 data)
        data_uri = f"data:audio/wav;base64,{b64_str}"

        # 构建DashScope聊天补全API URL
        # Build DashScope chat completions API URL
        url = f"{self.base_url}/chat/completions"
        # 构建请求头
        # Build request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",      # 认证令牌 / Auth token
            "Content-Type": "application/json",             # 内容类型为JSON / Content type JSON
        }
        # 构建请求负载
        # Build request payload
        payload = {
            "model": self.model,                            # 模型名称 / Model name
            "messages": [
                {
                    "role": "user",                         # 角色为用户 / Role is user
                    "content": [
                        {
                            "type": "input_audio",          # 内容类型为输入音频 / Content type input audio
                            "input_audio": {
                                "data": data_uri,           # 音频数据（Data URI格式） / Audio data (Data URI format)
                            },
                        }
                    ],
                }
            ],
            "stream": False,                                # 不使用流式响应 / Don't use streaming response
            "extra_body": {
                "asr_options": {
                    "enable_itn": False,                    # 不启用逆文本规范化 / Don't enable inverse text normalization
                }
            },
        }

        try:
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
                # Check if choices is not empty
                if choices:
                    # 提取第一个choice中的消息内容
                    # Extract message content from first choice
                    content = choices[0].get("message", {}).get("content", "")
                    # 检查内容是否非空
                    # Check if content is not empty
                    if content:
                        # 记录识别成功日志
                        # Log recognition success
                        logger.info("DashScope识别成功: %s", content[:30])
                        # 返回识别文本
                        # Return recognition text
                        return content
                # 记录返回空结果的警告
                # Log warning for returning empty result
                logger.warning("DashScope返回空结果: %s", response.text[:200])
            else:
                # 记录请求失败日志（包含状态码和响应内容）
                # Log request failure (includes status code and response content)
                logger.error("DashScope请求失败: %d %s", response.status_code, response.text[:200])
        except Exception as e:
            # 记录调用异常日志
            # Log call exception
            logger.error("DashScope调用异常: %s", e)
        # 失败时返回空字符串
        # Return empty string on failure
        return ""

    def _call_openai(self, client, wav_buffer) -> str:
        # 调用OpenAI标准API进行语音识别
        # Call OpenAI standard API for speech recognition
        # client: HTTP客户端
        # client: HTTP client
        # wav_buffer: WAV音频数据缓冲区
        # wav_buffer: WAV audio data buffer
        
        # 构建请求头
        # Build request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",      # 认证令牌 / Auth token
        }
        # 构建表单文件数据
        # Build form file data
        files = {
            "file": ("audio.wav", wav_buffer, "audio/wav"), # 音频文件 / Audio file
            "model": (None, self.model),                    # 模型名称 / Model name
            "response_format": (None, "verbose_json"),      # 响应格式为详细JSON / Response format verbose JSON
        }

        # 构建音频转录API URL
        # Build audio transcriptions API URL
        url = f"{self.base_url}/audio/transcriptions"
        try:
            # 发送POST请求（包含文件上传）
            # Send POST request (includes file upload)
            response = client.post(url, headers=headers, files=files)
            # 检查响应状态码是否为200（成功）
            # Check if response status code is 200 (success)
            if response.status_code == 200:
                # 解析JSON响应
                # Parse JSON response
                result = response.json()
                # 提取识别文本
                # Extract recognition text
                text = result.get("text", "")
                # 检查文本是否非空
                # Check if text is not empty
                if text:
                    # 记录识别成功日志
                    # Log recognition success
                    logger.info("OpenAI ASR识别成功: %s", text[:30])
                    # 返回识别文本
                    # Return recognition text
                    return text
            else:
                # 记录请求失败日志
                # Log request failure
                logger.error("OpenAI ASR请求失败: %d %s", response.status_code, response.text[:200])
        except Exception as e:
            # 记录调用异常日志
            # Log call exception
            logger.error("OpenAI ASR调用异常: %s", e)
        # 失败时返回空字符串
        # Return empty string on failure
        return ""

    async def send_audio(self, audio_data: bytes, is_last: bool = False):
        # 发送音频数据到处理队列
        # Send audio data to processing queue
        # audio_data: 音频字节数据
        # audio_data: audio byte data
        # is_last: 是否为最后一包（此实现中未使用）
        # is_last: whether this is the last packet (not used in this implementation)
        
        # 检查音频数据是否非空
        # Check if audio data is not empty
        if audio_data:
            try:
                # 将音频数据放入队列（非阻塞）
                # Put audio data into queue (non-blocking)
                self._audio_queue.put_nowait(audio_data)
            except queue.Full:
                # 队列已满时记录警告日志
                # Log warning when queue is full
                logger.warning("OpenAI兼容ASR: 音频队列已满，丢弃数据")

    async def receive_result(self) -> dict:
        # 从结果队列获取识别结果
        # Get recognition result from result queue
        try:
            # 尝试非阻塞获取结果
            # Try to get result non-blocking
            return self._result_queue.get_nowait()
        except queue.Empty:
            # 队列为空时返回空字典
            # Return empty dict when queue is empty
            return {}

    async def close(self):
        # 关闭OpenAI兼容ASR
        # Close OpenAI compatible ASR
        # 设置运行状态为False，停止处理循环
        # Set running state to False, stop processing loop
        self._running = False
        # 检查处理线程是否存在
        # Check if processing thread exists
        if self._thread:
            # 等待线程结束，超时时间5秒
            # Wait for thread to end, timeout 5 seconds
            self._thread.join(timeout=5)
