# -*- coding: utf-8 -*-
# 语音输入引擎模块 - 协调ASR Provider和AudioRecorder，处理识别结果
# 录音期间只收集音频，不实时识别，等停止后再统一上传识别
# 识别逻辑已拆分到recognizer.py
# Voice Input Engine Module - coordinates ASR Provider and AudioRecorder, handles recognition results
# During recording, only collects audio, no real-time recognition, uploads for recognition after stopping
# Recognition logic has been split to recognizer.py

# 导入异步操作支持库
# Import async operation support library
import asyncio
# 导入日志记录库
# Import logging library
import logging
# 导入线程安全队列库
# Import thread-safe queue library
import queue
# 导入多线程支持库
# Import threading support library
import threading
# 导入时间库（用于stop中的短暂等待）
# Import time library (for brief sleep in stop)
import time

# 从audio_recorder模块导入音频录制器类
# Import audio recorder class from audio_recorder module
from voiceinput.audio_recorder import AudioRecorder
# 从recognizer模块导入音频识别器类（识别逻辑已拆分）
# Import audio recognizer class from recognizer module (recognition logic split out)
from voiceinput.recognizer import AudioRecognizer

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


class VoiceInputEngine:
    # 语音输入引擎类 - 核心处理模块
    # 负责协调音频录制、ASR识别和结果回调
    # 识别逻辑委托给AudioRecognizer类
    # Voice Input Engine class - core processing module
    # Responsible for coordinating audio recording, ASR recognition and result callbacks
    # Recognition logic delegated to AudioRecognizer class

    def __init__(self, config: dict):
        # 初始化语音输入引擎
        # config: 配置字典，包含ASR提供商类型和认证信息等
        # Initialize voice input engine
        # config: configuration dictionary, contains ASR provider type and authentication info, etc.

        # 保存配置字典
        # Save configuration dictionary
        self.config = config
        # 初始化音频录制器为空
        # Initialize audio recorder to None
        self.recorder: AudioRecorder = None
        # 初始化运行状态为False
        # Initialize running state to False
        self._running = False
        # 初始化音频队列为空
        # Initialize audio queue to None
        self._audio_queue: queue.Queue = None
        # 初始化异步事件循环为空
        # Initialize async event loop to None
        self._loop: asyncio.AbstractEventLoop = None
        # 初始化工作线程为空
        # Initialize worker thread to None
        self._thread: threading.Thread = None
        # 初始化识别文本为空字符串
        # Initialize recognized text to empty string
        self._recognized_text = ""
        # 初始化最后确认文本为空字符串
        # Initialize last confirmed text to empty string
        self._last_confirmed_text = ""
        # 初始化结果回调函数为空
        # Initialize result callback function to None
        self._on_result_callback = None
        # 初始化状态回调函数为空
        # Initialize status callback function to None
        self._on_status_callback = None
        # 初始化错误回调函数为空
        # Initialize error callback function to None
        self._on_error_callback = None
        # 初始化停止事件为空
        # Initialize stop event to None
        self._stop_event: asyncio.Event = None
        # 初始化录制的音频块列表为空
        # Initialize recorded audio chunks list to None
        self._audio_chunks: list = []

    def set_callbacks(self, on_result=None, on_status=None, on_error=None):
        # 设置回调函数
        # on_result: 识别结果回调函数，接收(text, is_final)参数
        # on_status: 状态变更回调函数，接收(status)参数
        # on_error: 错误回调函数，接收(error)参数
        # Set callback functions
        # on_result: recognition result callback, receives (text, is_final) parameters
        # on_status: status change callback, receives (status) parameter
        # on_error: error callback, receives (error) parameter

        # 保存结果回调函数
        # Save result callback function
        self._on_result_callback = on_result
        # 保存状态回调函数
        # Save status callback function
        self._on_status_callback = on_status
        # 保存错误回调函数
        # Save error callback function
        self._on_error_callback = on_error

    def start(self):
        # 启动语音输入引擎
        # 创建并启动引擎线程，开始音频录制
        # Start voice input engine
        # Create and start engine thread, begin audio recording

        # 检查引擎是否已在运行
        # Check if engine is already running
        if self._running:
            # 记录警告日志并忽略重复启动
            # Log warning and ignore duplicate start
            logger.warning("引擎: 引擎已在运行中，忽略重复启动")
            return
        # 设置运行状态为True
        # Set running state to True
        self._running = True
        # 清空识别文本
        # Clear recognized text
        self._recognized_text = ""
        # 清空最后确认文本
        # Clear last confirmed text
        self._last_confirmed_text = ""
        # 清空音频块列表
        # Clear audio chunks list
        self._audio_chunks = []
        # 创建录音就绪事件（用于等待录音设备初始化完成）
        # Create recording ready event (used to wait for recording device initialization)
        self._ready_event = threading.Event()
        self._ready_event.clear()
        # 获取ASR提供商类型
        # Get ASR provider type
        provider_type = self.config.get("asr_provider", "doubao")
        # 记录启动日志
        # Log start
        logger.info("引擎: 启动语音输入引擎 (ASR提供商: %s)", provider_type)
        # 记录创建线程日志
        # Log creating thread
        logger.info("引擎: 创建引擎线程")
        # 创建引擎线程，目标函数为_run_loop，设置为守护线程
        # Create engine thread, target function is _run_loop, set as daemon thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        # 启动线程
        # Start thread
        self._thread.start()
        # 等待录音设备就绪（最多等待3秒）
        # Wait for recording device to be ready (up to 3 seconds)
        if self._ready_event.wait(timeout=3.0):
            # 记录录音已就绪日志
            # Log recording ready
            logger.info("引擎: 录音设备已就绪")
        else:
            # 记录等待超时警告
            # Log wait timeout warning
            logger.warning("引擎: 录音设备初始化超时（3秒）")
        # 记录线程已启动日志
        # Log thread started
        logger.info("引擎: 引擎线程已启动")
        # 检查状态回调函数是否存在
        # Check if status callback function exists
        if self._on_status_callback:
            # 记录状态变更日志
            # Log status change
            logger.info("引擎: 通知状态变更 -> recording")
            # 调用状态回调函数，通知进入录音状态
            # Call status callback function, notify entering recording state
            self._on_status_callback("recording")
        # 记录引擎已启动日志
        # Log engine started
        logger.info("引擎: 语音输入引擎已启动")

    def stop(self):
        # 停止语音输入引擎
        # 停止录音、等待线程结束、清理资源
        # 确保所有资源被彻底清理，防止僵尸收集循环
        # Stop voice input engine
        # Stop recording, wait for thread to end, clean up resources
        # Ensure all resources are thoroughly cleaned up to prevent zombie collect loops

        # 检查引擎是否在运行
        # Check if engine is running
        if not self._running:
            # 记录日志并忽略停止请求
            # Log and ignore stop request
            logger.info("引擎: 引擎未在运行，忽略停止请求")
            return
        # 记录正在停止日志
        # Log stopping
        logger.info("引擎: 正在停止语音输入引擎...")
        # 第一步：先设置运行标志为False，让收集循环和录音循环尽快退出
        # Step 1: Set running flag to False first, so collect loop and record loop exit ASAP
        self._running = False
        # 第二步：停止录音器
        # Step 2: Stop recorder
        if self.recorder:
            # 记录停止录音日志
            # Log stopping recording
            logger.info("引擎: 停止音频录制")
            # 停止音频录制
            # Stop audio recording
            self.recorder.stop()
            # 清空录音器引用
            # Clear recorder reference
            self.recorder = None
        # 第三步：清空音频队列，防止收集循环继续处理残留数据
        # Step 3: Clear audio queue to prevent collect loop from processing residual data
        if self._audio_queue:
            try:
                while not self._audio_queue.empty():
                    self._audio_queue.get_nowait()
                logger.info("引擎: 音频队列已清空")
            except Exception as e:
                # 记录清空队列异常（不影响后续停止流程）
                # Log queue clear exception (doesn't affect subsequent stop flow)
                logger.debug("引擎: 清空音频队列异常: %s", e)
        # 第四步：检查停止事件和事件循环是否存在且正在运行
        # Step 4: Check stop event and event loop exist and are running
        if self._stop_event and self._loop and self._loop.is_running():
            # 记录发送停止事件日志
            # Log sending stop event
            logger.info("引擎: 发送停止事件到事件循环")
            # 线程安全地设置停止事件
            # Thread-safely set stop event
            self._loop.call_soon_threadsafe(self._stop_event.set)
        else:
            # 记录事件循环未运行日志
            # Log event loop not running
            logger.info("引擎: 事件循环未运行或未创建")
        # 第五步：等待引擎线程结束
        # Step 5: Wait for engine thread to end
        if self._thread:
            # 记录等待线程结束日志
            # Log waiting for thread to end
            logger.info("引擎: 等待引擎线程结束...")
            # 等待线程结束，超时时间15秒
            # Wait for thread to end, timeout 15 seconds
            self._thread.join(timeout=15)
            # 检查线程是否已结束
            # Check if thread has ended
            if not self._thread.is_alive():
                # 记录线程已结束日志
                # Log thread ended
                logger.info("引擎: 引擎线程已结束")
            else:
                # 记录线程超时警告
                # Log thread timeout warning
                logger.warning("引擎: 引擎线程超时")
        # 第六步：强制关闭事件循环（防止僵尸协程）
        # Step 6: Force close event loop (prevent zombie coroutines)
        if self._loop:
            try:
                # 如果事件循环还在运行，先请求停止，等待它停下来再关闭
                # If event loop is still running, request stop first, wait for it to stop before closing
                if self._loop.is_running():
                    self._loop.call_soon_threadsafe(self._loop.stop)
                    logger.info("引擎: 事件循环已请求停止")
                    # 等待事件循环停止（最多等 2 秒）
                    # Wait for event loop to stop (max 2 seconds)
                    for _ in range(20):
                        if not self._loop.is_running():
                            break
                        time.sleep(0.1)
                # 如果事件循环未关闭，关闭它
                # If event loop is not closed, close it
                if not self._loop.is_closed():
                    self._loop.close()
                    logger.info("引擎: 事件循环已关闭")
            except Exception as e:
                logger.warning("引擎: 关闭事件循环异常: %s", e)
            finally:
                self._loop = None
        # 检查状态回调函数是否存在
        # Check if status callback exists
        if self._on_status_callback:
            # 记录状态变更日志
            # Log status change
            logger.info("引擎: 通知状态变更 -> idle")
            # 调用状态回调函数，通知进入空闲状态
            # Call status callback to notify idle state
            self._on_status_callback("idle")
        # 记录引擎已停止日志
        # Log engine stopped
        logger.info("引擎: 语音输入引擎已停止")

    def _run_loop(self):
        # 运行异步事件循环
        # 此函数在独立线程中运行，创建并运行异步事件循环
        # Run async event loop
        # This function runs in a separate thread, creates and runs async event loop

        # 创建新的异步事件循环
        # Create new async event loop
        self._loop = asyncio.new_event_loop()
        # 设置当前线程的事件循环
        # Set current thread's event loop
        asyncio.set_event_loop(self._loop)
        try:
            # 运行异步主函数直到完成
            # Run async main function until complete
            self._loop.run_until_complete(self._async_run())
        except Exception as e:
            # 捕获异常并记录错误日志
            # Catch exception and log error
            logger.error("语音引擎运行异常: %s", e)
        finally:
            # 清理所有未完成的任务
            # Clean up all unfinished tasks
            try:
                # 获取所有未完成的任务
                # Get all unfinished tasks
                pending = asyncio.all_tasks(self._loop)
                # 遍历并取消所有任务
                # Iterate and cancel all tasks
                for task in pending:
                    task.cancel()
                # 如果有未完成的任务，等待它们完成
                # If there are unfinished tasks, wait for them to complete
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                # 记录清理任务异常（不中断退出流程）
                # Log cleanup exception (don't interrupt exit flow)
                logger.debug("引擎: 清理任务异常: %s", e)
            # 关闭事件循环（_loop 可能在超时后被置为 None）
            # Close event loop (_loop may be set to None after timeout)
            if self._loop is not None:
                try:
                    if not self._loop.is_closed():
                        self._loop.close()
                except Exception:
                    pass

    async def _async_run(self):
        # 异步运行主逻辑
        # 启动音频录制、收集音频块、停止后统一识别
        # 识别逻辑委托给AudioRecognizer类
        # Async run main logic
        # Start audio recording, collect audio chunks, recognize after stopping
        # Recognition logic delegated to AudioRecognizer class

        # 创建停止事件
        # Create stop event
        self._stop_event = asyncio.Event()
        # 从配置中获取采样率，默认16000Hz
        # Get sample rate from config, default 16000Hz
        sample_rate = self.config.get("sample_rate", 16000)
        # 从配置中获取块大小，默认3200字节
        # Get chunk size from config, default 3200 bytes
        chunk_size = self.config.get("chunk_size", 3200)
        # 创建音频队列，最大容量200
        # Create audio queue, max capacity 200
        self._audio_queue = queue.Queue(maxsize=200)
        # 创建音频录制器实例
        # Create audio recorder instance
        self.recorder = AudioRecorder(sample_rate=sample_rate, chunk_size=chunk_size)
        # 将录音就绪事件传递给录音器
        # Pass recording ready event to recorder
        self.recorder._ready_event = self._ready_event
        # 启动音频录制，将音频数据放入队列
        # Start audio recording, put audio data into queue
        self.recorder.start(self._audio_queue)
        # 记录录音启动日志
        # Log recording started
        logger.info("引擎: 音频录制已启动 (采样率=%d, 块大小=%d)", sample_rate, chunk_size)

        # 创建音频收集任务，录音期间只收集音频块，不实时识别
        # Create audio collection task, only collect audio chunks during recording, no real-time recognition
        collect_task = asyncio.ensure_future(self._collect_audio_loop())

        # 录音时长上限保护：防止用户忘记停止录音，导致长时间空录浪费 API 调用和 CPU
        # 默认 60 秒自动停止，可通过 config 的 max_recording_duration 配置
        # Recording duration limit: prevent user from forgetting to stop, wasting API calls and CPU
        # Default 60s auto-stop, configurable via max_recording_duration in config
        max_duration = self.config.get("max_recording_duration", 60)

        try:
            # 等待停止事件被设置，最多等待 max_duration 秒
            # Wait for stop event to be set, up to max_duration seconds
            await asyncio.wait_for(self._stop_event.wait(), timeout=max_duration)
        except asyncio.TimeoutError:
            # 录音超时自动停止
            # Recording timed out, auto-stop
            logger.warning("引擎: 录音超过 %d 秒，自动停止", max_duration)
            # 通知 UI 状态变更（超时自动停止）
            # Notify UI state change (timeout auto-stop)
            if self._on_status_callback:
                self._on_status_callback("timeout")
        finally:
            # 记录收到停止信号日志
            # Log received stop signal
            logger.info("引擎: 收到停止信号，开始清理...")
            # 取消音频收集任务
            # Cancel audio collection task
            collect_task.cancel()
            # 等待收集任务结束
            # Wait for collection task to end
            try:
                await asyncio.wait_for(collect_task, timeout=3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                # 忽略超时和取消异常
                # Ignore timeout and cancel exceptions
                pass
            # 停止录音器（防止超时自动停止后麦克风仍开着）
            # Stop recorder (prevent mic staying on after timeout auto-stop)
            if self.recorder:
                try:
                    self.recorder.stop()
                    self.recorder = None
                except Exception as e:
                    logger.warning("引擎: 停止录音器异常: %s", e)

        # 录音结束后，统一识别所有音频（放在finally之外，避免识别异常导致recorder泄漏）
        # Recognize all audio after recording (outside finally to avoid recorder leak on recognition error)
        if self._audio_chunks:
            # 计算音频块数量和总字节数
            # Calculate audio chunk count and total bytes
            total_bytes = sum(len(c) for c in self._audio_chunks)
            # 记录开始识别日志
            # Log start recognition
            logger.info("引擎: 开始识别，共 %d 个音频块，%d 字节", len(self._audio_chunks), total_bytes)
            # 创建音频识别器实例，委托识别逻辑
            # Create audio recognizer instance, delegate recognition logic
            recognizer = AudioRecognizer(self.config, self._on_result_callback)
            try:
                # 调用识别器的识别方法
                # Call recognizer's recognize method
                await recognizer.recognize(self._audio_chunks)
            except Exception as e:
                logger.error("引擎: 识别过程异常: %s", e)
        else:
            # 记录没有录制到音频日志
            # Log no audio recorded
            logger.info("引擎: 没有录制到音频数据")

        # 停止并清理录音器（无论识别成功与否都要执行）
        # Stop and clean up recorder (must execute regardless of recognition success)
        if self.recorder:
            self.recorder.stop()
            self.recorder = None

    async def _collect_audio_loop(self):
        # 录音期间只收集音频块
        # 从音频队列中获取数据并保存到音频块列表
        # 当 _running 为 False 或任务被取消时退出
        # Collect audio chunks during recording
        # Get data from audio queue and save to audio chunks list
        # Exit when _running is False or task is cancelled

        # 初始化音频块计数器
        # Initialize audio chunk counter
        chunk_count = 0
        try:
            # 主循环：当运行状态为True时持续运行
            # Main loop: continue while running state is True
            while self._running:
                try:
                    # 尝试从音频队列非阻塞获取数据
                    # Try to get data from audio queue non-blocking
                    audio_data = self._audio_queue.get_nowait()
                    # 将音频数据追加到音频块列表
                    # Append audio data to audio chunks list
                    self._audio_chunks.append(audio_data)
                    # 增加音频块计数
                    # Increment audio chunk counter
                    chunk_count += 1
                    # 每50个块记录一次日志
                    # Log every 50 chunks
                    if chunk_count % 50 == 0:
                        logger.info("引擎: 已收集 %d 个音频块", chunk_count)
                except queue.Empty:
                    # 队列为空时等待20毫秒
                    # Wait 20ms when queue is empty
                    await asyncio.sleep(0.02)
                except Exception as e:
                    # 记录收集音频异常日志
                    # Log audio collection exception
                    logger.error("引擎: 收集音频异常: %s", e)
                    # 跳出循环
                    # Break out of loop
                    break
        except asyncio.CancelledError:
            # 记录循环被取消日志
            # Log loop cancelled
            logger.info("引擎: 音频收集循环被取消")
            # 不再重新抛出 CancelledError，让任务正常结束
            # Don't re-raise CancelledError, let task end normally
        # 记录循环结束日志
        # Log loop ended
        logger.info("引擎: 音频收集循环结束，共收集 %d 个块", chunk_count)
