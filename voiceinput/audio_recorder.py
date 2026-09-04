# -*- coding: utf-8 -*-
# 音频录制模块 - 使用PyAudio从麦克风采集PCM音频
# Audio recording module - capture PCM audio from microphone using PyAudio

# 导入日志记录库
# Import logging library
import logging
# 导入线程安全队列库
# Import thread-safe queue library
import queue
# 导入多线程支持库
# Import threading support library
import threading

# 导入音频处理库
# Import audio processing library
import pyaudio

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


class AudioRecorder:
    # 音频录制类 - 负责从麦克风采集音频数据
    # Audio recording class - responsible for capturing audio data from microphone
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 3200):
        # 初始化音频录制器
        # sample_rate: 采样率，默认16000Hz
        # channels: 声道数，默认1（单声道）
        # chunk_size: 每次读取的音频块大小，默认3200字节
        # Initialize audio recorder
        # sample_rate: sample rate, default 16000Hz
        # channels: number of channels, default 1 (mono)
        # chunk_size: audio chunk size per read, default 3200 bytes
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        # PyAudio实例
        # PyAudio instance
        self.pa = None
        # 音频流对象
        # Audio stream object
        self.stream = None
        # 录制状态标志
        # Recording status flag
        self._recording = False
        # 音频数据队列
        # Audio data queue
        self._audio_queue: queue.Queue = None
        # 录音就绪事件（用于通知录音设备已初始化完成）
        # Recording ready event (used to notify that recording device is initialized)
        self._ready_event = None

    def start(self, audio_queue: queue.Queue):
        # 启动音频录制
        # audio_queue: 用于存储录制音频数据的队列
        # Start audio recording
        # audio_queue: queue for storing recorded audio data
        logger.info("录音器: 开始音频录制 (采样率: %d, 块大小: %d)", self.sample_rate, self.chunk_size)
        # 设置录制状态为True
        # Set recording status to True
        self._recording = True
        # 保存音频队列引用
        # Save audio queue reference
        self._audio_queue = audio_queue
        logger.info("录音器: 初始化 PyAudio...")
        # 创建PyAudio实例
        # Create PyAudio instance
        self.pa = pyaudio.PyAudio()
        logger.info("录音器: PyAudio 初始化成功")
        logger.info("录音器: 打开音频流 (格式: paInt16, 声道: %d, 采样率: %d)", self.channels, self.sample_rate)
        # 打开音频输入流
        # Open audio input stream
        self.stream = self.pa.open(
            format=pyaudio.paInt16,           # 16位PCM格式 / 16-bit PCM format
            channels=self.channels,           # 声道数 / Number of channels
            rate=self.sample_rate,            # 采样率 / Sample rate
            input=True,                       # 启用输入 / Enable input
            frames_per_buffer=self.chunk_size, # 缓冲区大小 / Buffer size
        )
        logger.info("录音器: 音频流已打开")
        # 启动录制循环线程（守护线程，主程序退出时自动结束）
        # Start recording loop thread (daemon thread, ends automatically when main program exits)
        threading.Thread(target=self._record_loop, daemon=True).start()
        logger.info("录音器: 录制循环线程已启动")
        # 通知录音设备已就绪
        # Notify that recording device is ready
        if self._ready_event is not None:
            self._ready_event.set()
        logger.info("录音器: 音频录制已启动 (采样率: %d, 块大小: %d)", self.sample_rate, self.chunk_size)

    def _record_loop(self):
        # 录制循环 - 持续从音频流读取数据并放入队列
        # Recording loop - continuously read data from audio stream and put into queue
        chunk_count = 0
        logger.info("录音器: 录制循环开始")
        # 当录制状态为True时持续运行
        # Continue running when recording status is True
        while self._recording:
            try:
                # 从音频流读取一个块的数据
                # Read one chunk of data from audio stream
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                chunk_count += 1
                # 每100个块记录一次调试日志
                # Log debug message every 100 chunks
                if chunk_count % 100 == 0:
                    logger.debug("录音器: 已录制 %d 个音频块", chunk_count)
                # 将音频数据放入队列
                # Put audio data into queue
                if self._audio_queue is not None:
                    try:
                        # 尝试立即放入队列
                        # Try to put into queue immediately
                        self._audio_queue.put_nowait(audio_data)
                    except queue.Full:
                        # 队列满时，先取出最旧的数据
                        # When queue is full, first remove oldest data
                        try:
                            self._audio_queue.get_nowait()
                        except queue.Empty:
                            pass
                        # 再放入新数据
                        # Then put new data
                        self._audio_queue.put_nowait(audio_data)
            except OSError as e:
                # 捕获操作系统错误（通常是音频设备问题）
                # Catch OS error (usually audio device issue)
                logger.error("录音器: 录音异常 (OSError): %s", e)
                break
            except Exception as e:
                # 捕获其他异常
                # Catch other exceptions
                logger.error("录音器: 录音异常: %s", e)
                break
        logger.info("录音器: 录制循环结束，共录制 %d 个块", chunk_count)

    def stop(self):
        # 停止音频录制
        # Stop audio recording
        logger.info("录音器: 正在停止音频录制...")
        # 设置录制状态为False
        # Set recording status to False
        self._recording = False
        # 关闭音频流
        # Close audio stream
        if self.stream:
            try:
                logger.info("录音器: 停止音频流...")
                # 停止音频流
                # Stop audio stream
                self.stream.stop_stream()
                logger.info("录音器: 关闭音频流...")
                # 关闭音频流
                # Close audio stream
                self.stream.close()
                logger.info("录音器: 音频流已关闭")
            except Exception as e:
                logger.error("录音器: 停止音频流异常: %s", e)
        # 终止PyAudio
        # Terminate PyAudio
        if self.pa:
            try:
                logger.info("录音器: 终止 PyAudio...")
                # 终止PyAudio实例
                # Terminate PyAudio instance
                self.pa.terminate()
                logger.info("录音器: PyAudio 已终止")
            except Exception as e:
                logger.error("录音器: 终止 PyAudio 异常: %s", e)
        # 清空引用
        # Clear references
        self.stream = None
        self.pa = None
        logger.info("录音器: 音频录制已停止")

    @property
    def is_recording(self) -> bool:
        # 获取当前录制状态
        # Get current recording status
        return self._recording
