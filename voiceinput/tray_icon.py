# -*- coding: utf-8 -*-
# Windows托盘图标模块 - 使用win32gui实现
# 支持左键单击打开窗口，右键弹出菜单
# Windows Tray Icon Module - Implemented using win32gui
# Supports left-click to open window, right-click for popup menu

# 导入日志记录库
# Import logging library
import logging
# 导入多线程支持库
# Import threading support library
import threading
# 导入Windows GUI API库
# Import Windows GUI API library
import win32gui
# 导入Windows常量定义库
# Import Windows constant definition library
import win32con
# 导入Windows API库
# Import Windows API library
import win32api
# 导入操作系统接口库
# Import operating system interface library
import os
# 导入临时文件处理库
# Import temporary file processing library
import tempfile
# 导入Python图像处理库
# Import Python image processing library
from PIL import Image

# 从i18n模块导入翻译函数
# Import translation functions from i18n module
from .i18n import _

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 自定义托盘消息ID定义 ==========
# ========== Custom tray message ID definitions ==========
# 定义自定义托盘消息ID，基于WM_USER + 1
# Define custom tray message ID, based on WM_USER + 1
WM_TRAYICON = win32con.WM_USER + 1


def _pil_to_hicon(img):
    # 将PIL图片转换为Windows图标句柄
    # img: PIL Image对象，如果为空则创建默认灰色图标
    # 返回Windows图标句柄（HICON）
    # Convert PIL image to Windows icon handle
    # img: PIL Image object, create default gray icon if empty
    # Return Windows icon handle (HICON)
    
    # 检查图片是否为空
    # Check if image is empty
    if img is None:
        # 如果为空，创建64x64的灰色RGBA图片
        # If empty, create 64x64 gray RGBA image
        img = Image.new("RGBA", (64, 64), (80, 80, 80, 255))

    # 将图片尺寸调整为64x64像素，使用LANCZOS算法保证质量
    # Resize image to 64x64 pixels, use LANCZOS algorithm for quality
    img = img.resize((64, 64), Image.LANCZOS)

    # 构建临时ICO文件路径
    # Build temporary ICO file path
    tmp_path = os.path.join(tempfile.gettempdir(), "voiceinput_tray.ico")
    # 将图片保存为临时ICO文件
    # Save image as temporary ICO file
    img.save(tmp_path, format="ICO", sizes=[(64, 64)])

    # 从临时文件加载Windows图标
    # Load Windows icon from temporary file
    hicon = win32gui.LoadImage(
        0,                                          # 模块句柄为0表示从文件加载
                                                    # Module handle 0 means load from file
        tmp_path,                                   # 临时ICO文件路径
                                                    # Temporary ICO file path
        win32con.IMAGE_ICON,                        # 加载类型为图标
                                                    # Load type is icon
        0, 0,                                       # 宽高为0表示使用默认尺寸
                                                    # Width and height 0 means use default size
        win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE  # 标志：从文件加载+使用默认尺寸
                                                            # Flags: load from file + use default size
    )

    # 尝试删除临时ICO文件
    # Try to delete temporary ICO file
    try:
        os.remove(tmp_path)
    except Exception as e:
        # 删除临时ICO文件失败时记录调试日志，便于排查问题但不影响图标创建主流程
        # Record debug log when deleting temporary ICO file fails for troubleshooting without affecting icon creation main flow
        logger.debug("托盘: 删除临时ICO文件异常: %s", e)

    # 返回Windows图标句柄
    # Return Windows icon handle
    return hicon


class TrayIcon:
    # Windows托盘图标类
    # 使用win32gui实现系统托盘功能，支持左键单击和右键菜单
    # Windows tray icon class
    # Uses win32gui for system tray functionality, supports left-click and right-click menu

    def __init__(self, title="语音输入", on_left_click=None, on_quit=None,
                 on_add_hotword=None, on_copy_result=None, on_clear_llm_history=None):
        # 初始化托盘图标
        # title: 托盘图标提示文字
        # on_left_click: 左键点击时的回调函数
        # on_quit: 退出时的回调函数
        # on_add_hotword: 添加热词的回调函数
        # on_copy_result: 复制结果的回调函数
        # on_clear_llm_history: 清除LLM记忆的回调函数
        # Initialize tray icon
        # title: tray icon tooltip text
        # on_left_click: callback function on left click
        # on_quit: callback function on quit
        # on_add_hotword: callback function for adding hotword
        # on_copy_result: callback function for copying result
        # on_clear_llm_history: callback function for clearing LLM history

        # 保存托盘提示文字
        # Save tray tooltip text
        self.title = title
        # 保存左键点击回调函数
        # Save left click callback function
        self.on_left_click = on_left_click
        # 保存退出回调函数
        # Save quit callback function
        self.on_quit = on_quit
        # 保存添加热词回调函数
        # Save add hotword callback function
        self.on_add_hotword = on_add_hotword
        # 保存复制结果回调函数
        # Save copy result callback function
        self.on_copy_result = on_copy_result
        # 保存清除LLM记忆回调函数
        # Save clear LLM history callback function
        self.on_clear_llm_history = on_clear_llm_history
        # 初始化窗口句柄为空
        # Initialize window handle to None
        self._hwnd = None
        # 初始化运行状态为False
        # Initialize running state to False
        self._running = False
        # 初始化托盘图标ID为空
        # Initialize tray icon ID to None
        self._nid = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        # 窗口过程函数 - 处理托盘消息
        # hwnd: 窗口句柄
        # msg: 消息类型
        # wparam: 消息参数1
        # lparam: 消息参数2
        # 返回消息处理结果
        # Window procedure function - handle tray messages
        # hwnd: window handle
        # msg: message type
        # wparam: message parameter 1
        # lparam: message parameter 2
        # Return message processing result
        
        # 判断是否为自定义托盘消息
        # Check if custom tray message
        if msg == WM_TRAYICON:
            # 判断是否为左键单击释放消息
            # Check if left button click release message
            if lparam == win32con.WM_LBUTTONUP:
                # 左键单击：直接显示主窗口
                # Left click: show main window directly
                if self.on_left_click:
                    self.on_left_click()
            # 判断是否为右键单击释放消息
            # Check if right button click release message
            elif lparam == win32con.WM_RBUTTONUP:
                # 调用显示右键菜单函数
                # Call show right-click menu function
                self._show_menu(hwnd)
            # 判断是否为左键双击消息
            # Check if left button double-click message
            elif lparam == win32con.WM_LBUTTONDBLCLK:
                # 左键双击：同样显示主窗口（和单击行为一致）
                # Left double-click: show main window too (same behavior as click)
                if self.on_left_click:
                    self.on_left_click()
        # 判断是否为命令消息（菜单项点击）
        # Check if command message (menu item click)
        elif msg == win32con.WM_COMMAND:
            # 判断是否为退出菜单项（ID=1001）
            # Check if quit menu item (ID=1001)
            if wparam == 1001:
                # 检查退出回调是否存在
                # Check if quit callback exists
                if self.on_quit:
                    # 调用退出回调函数
                    # Call quit callback function
                    self.on_quit()
            # 判断是否为添加热词菜单项（ID=1002）
            # Check if add hotword menu item (ID=1002)
            elif wparam == 1002:
                # 检查添加热词回调是否存在
                # Check if add hotword callback exists
                if self.on_add_hotword:
                    # 调用添加热词回调函数
                    # Call add hotword callback function
                    self.on_add_hotword()
            # 判断是否为复制结果菜单项（ID=1003）
            # Check if copy result menu item (ID=1003)
            elif wparam == 1003:
                # 检查复制结果回调是否存在
                # Check if copy result callback exists
                if self.on_copy_result:
                    # 调用复制结果回调函数
                    # Call copy result callback function
                    self.on_copy_result()
            # 判断是否为清除LLM记忆菜单项（ID=1004）
            # Check if clear LLM history menu item (ID=1004)
            elif wparam == 1004:
                # 检查清除LLM记忆回调是否存在
                # Check if clear LLM history callback exists
                if self.on_clear_llm_history:
                    # 调用清除LLM记忆回调函数
                    # Call clear LLM history callback function
                    self.on_clear_llm_history()
        # 调用默认窗口过程处理其他消息
        # Call default window procedure to handle other messages
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_menu(self, hwnd):
        # 显示右键菜单
        # hwnd: 窗口句柄
        # Show right-click menu
        # hwnd: window handle
        
        try:
            # 创建弹出菜单（仅保留"退出"项，其余三项已移除）
            # Create popup menu (only "Quit" remains, other three items removed)
            menu = win32gui.CreatePopupMenu()
            # 添加"退出"菜单项，ID为1001
            # Add "Quit" menu item, ID=1001
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1001, _("tray.quit"))
            # 获取当前鼠标光标位置
            # Get current mouse cursor position
            x, y = win32gui.GetCursorPos()
            # 将窗口设置为前台窗口（确保菜单正确显示）
            # 注意：必须先设置前台窗口，否则菜单会立即消失
            # Set window as foreground window (ensure menu displays correctly)
            # Note: Must set foreground window first, otherwise menu will disappear immediately
            win32gui.SetForegroundWindow(hwnd)
            # 在鼠标位置显示弹出菜单
            # Show popup menu at mouse position
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN | win32con.TPM_BOTTOMALIGN, x, y, 0, hwnd, None)
            # 发送空消息以刷新消息队列
            # Send null message to refresh message queue
            win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        except Exception as e:
            # 记录显示菜单失败日志
            # Log menu display failure
            logger.error("托盘: 显示右键菜单失败: %s", e)
        finally:
            # 销毁菜单对象释放资源（无论是否成功都要执行）
            # Destroy menu object to release resources (execute regardless of success)
            try:
                win32gui.DestroyMenu(menu)
            except Exception as e:
                # 销毁菜单对象失败时记录调试日志，资源释放异常不影响后续消息处理
                # Record debug log when destroying menu object fails, resource release exception doesn't affect subsequent message processing
                logger.debug("托盘: 销毁菜单异常: %s", e)

    def run(self, icon=None):
        # 运行托盘事件循环
        # icon: 托盘图标图片（PIL Image对象）
        # Run tray event loop
        # icon: tray icon image (PIL Image object)
        
        # 设置运行状态为True
        # Set running state to True
        self._running = True

        # 创建窗口类结构
        # Create window class structure
        wc = win32gui.WNDCLASS()
        # 设置窗口过程函数为自定义处理函数
        wc.lpfnWndProc = self._wnd_proc
        # 设置窗口类名称
        wc.lpszClassName = "VoiceInputTray"
        # 获取当前模块句柄
        wc.hInstance = win32api.GetModuleHandle(None)
        # 加载默认箭头光标
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        # 设置窗口背景画刷
        wc.hbrBackground = win32con.COLOR_WINDOW

        # 注册窗口类
        class_atom = win32gui.RegisterClass(wc)
        # 创建隐藏窗口（用于接收托盘消息）
        self._hwnd = win32gui.CreateWindow(
            class_atom, "VoiceInputTray",                   # 窗口类名和窗口名
            win32con.WS_OVERLAPPEDWINDOW,                   # 窗口样式
            0, 0, 0, 0, 0, 0, wc.hInstance, None            # 位置、大小、父窗口等
        )

        # 将PIL图片转换为Windows图标句柄
        hicon = _pil_to_hicon(icon)

        # 构建托盘图标数据结构（NOTIFYICONDATA）
        self._nid = (self._hwnd, 0,
                     win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,  # 标志：图标+消息+提示
                     WM_TRAYICON, hicon, self.title)                                # 消息ID、图标句柄、提示文字
        # 向系统托盘添加图标
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self._nid)

        # 记录托盘启动日志
        logger.info("托盘: win32gui托盘已启动")

        # 消息循环：持续处理Windows消息
        while self._running:
            try:
                # 处理等待中的消息（非阻塞）
                win32gui.PumpWaitingMessages()
                # 导入时间库
                import time
                # 休眠50毫秒，降低CPU占用
                time.sleep(0.05)
            except Exception as e:
                # 记录消息循环异常日志
                logger.error("托盘: 消息循环异常: %s", e)
                # 跳出消息循环
                break

        # 清理资源：从系统托盘删除图标
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self._nid)
        except Exception as e:
            # 托盘图标可能已失效，忽略错误
            logger.warning("托盘: 清理托盘图标时出错: %s", e)
        # 销毁图标句柄释放GDI资源
        try:
            win32gui.DestroyIcon(hicon)
        except Exception as e:
            logger.warning("托盘: 销毁图标句柄时出错: %s", e)
        # 销毁隐藏窗口
        try:
            win32gui.DestroyWindow(self._hwnd)
        except Exception as e:
            logger.warning("托盘: 销毁窗口时出错: %s", e)
        # 注销窗口类（需要类名和模块句柄两个参数）
        try:
            win32gui.UnregisterClass(class_atom, wc.hInstance)
        except Exception as e:
            logger.warning("托盘: 注销窗口类时出错: %s", e)
        # 记录托盘停止日志
        logger.info("托盘: win32gui托盘已停止")

    def stop(self):
        # 停止托盘
        # 设置运行状态为False，使消息循环退出
        # 同时立即删除托盘图标，避免图标停留
        
        # 设置运行状态为False
        self._running = False
        # 立即删除托盘图标，避免图标在退出时停留
        if self._nid is not None:
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self._nid)
            except Exception as e:
                # 删除托盘图标失败时记录调试日志，退出阶段异常无需中断程序停止流程
                # Record debug log when deleting tray icon fails, exit phase exception doesn't need to interrupt program stop flow
                logger.debug("托盘: 删除托盘图标异常: %s", e)

    def update_icon(self, icon=None, title=None):
        # 更新托盘图标和标题
        # icon: 新的托盘图标图片（PIL Image对象）
        # title: 新的托盘提示文字
        
        # 检查托盘图标ID是否已初始化
        if self._nid is None:
            # 未初始化，直接返回
            return
        # 检查是否提供了新图标
        if icon:
            # 将新图片转换为Windows图标句柄
            hicon = _pil_to_hicon(icon)
            # 更新托盘图标数据结构（包含新图标）
            self._nid = (self._nid[0], self._nid[1],
                         win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,  # 标志
                         WM_TRAYICON, hicon, title or self.title)                        # 新图标和新标题
        else:
            # 没有新图标，只更新标题
            self._nid = (self._nid[0], self._nid[1],
                         win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,  # 标志
                         WM_TRAYICON, self._nid[4], title or self.title)                 # 保持原图标，更新标题
        # 检查是否提供了新标题
        if title:
            # 更新保存的标题
            self.title = title
        # 向系统发送修改托盘图标通知
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, self._nid)
