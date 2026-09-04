# -*- coding: utf-8 -*-
# 应用控制器模块 - 抽取 gui.py 中的纯业务逻辑
# 负责配置管理、自启动设置等不依赖 GUI 控件的逻辑
# 可被 gui.py 和 gui2.py（PySide6 版本）共同调用
# App controller module - extracts pure business logic from gui.py
# Responsible for config management, auto-start setup, etc., no GUI dependency
# Can be shared by gui.py and gui2.py (PySide6 version)

# 导入日志记录库
# Import logging library
import logging
# 导入操作系统接口库
# Import operating system interface library
import os
# 导入系统相关功能库
# Import system-related functionality library
import sys
# 导入多线程支持库
# Import threading library
import threading

# 从 autostart_helper 模块导入注册表自启动操作函数
# Import registry auto-start operations from autostart_helper module
from .autostart_helper import (
    set_autostart as registry_set_autostart,       # 写入注册表 Run 键
    remove_autostart as registry_remove_autostart, # 删除注册表 Run 键值
    get_command as registry_get_command,           # 获取自启动命令字符串
    is_registered as registry_is_registered,       # 检查是否已注册
)

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


class AppController:
    # 应用控制器类
    # 封装不依赖 GUI 控件的纯业务逻辑，方便 gui.py 和 gui2.py 共同调用
    # 所有方法均为静态方法，无需实例化即可使用
    # App controller class
    # Encapsulates pure business logic without GUI dependency
    # All methods are static, can be called without instantiation

    @staticmethod
    def save_config_to_file(config: dict, on_success=None, on_error=None):
        # 异步保存配置到文件（避免 IO 阻塞主线程导致界面卡顿）
        # config: 配置字典
        # on_success: 保存成功回调（无参数）
        # on_error: 保存失败回调（接收错误信息字符串）
        # Async save config to file (avoid IO blocking main thread causing UI lag)
        # config: config dict
        # on_success: success callback (no params)
        # on_error: error callback (receives error message string)

        # 制作配置快照（子线程读取，避免主线程同时修改）
        # Make config snapshot (read by worker thread, avoid concurrent modification)
        config_snapshot = config.copy()

        def _save_in_thread():
            # 子线程中执行文件写入
            # Execute file write in worker thread
            try:
                from .config import save_config
                save_config(config_snapshot)
                # 保存成功，调用成功回调
                if on_success:
                    on_success()
            except Exception as e:
                # 保存失败，记录日志并调用错误回调
                logger.error("配置保存失败: %s", e)
                if on_error:
                    on_error(str(e))

        # 启动守护线程（程序退出时自动结束）
        # Start daemon thread (auto-ends on program exit)
        threading.Thread(target=_save_in_thread, daemon=True).start()

    @staticmethod
    def _update_and_save(config: dict, key: str, value, warn_label: str):
        # 内部方法：更新配置项并保存到文件（合并6处重复代码）
        # config: 配置字典
        # key: 配置键名
        # value: 配置值
        # warn_label: 警告日志中的标签文字（如"主题"、"悬浮窗"）
        # Internal: update config item and save to file (merges 6 duplicated patterns)
        # config: config dict
        # key: config key name
        # value: config value
        # warn_label: label text in warning log (e.g. "theme", "floating")
        if not config:
            return
        config[key] = value
        try:
            from .config import save_config
            save_config(config)
        except Exception as e:
            logger.warning("保存%s配置失败: %s", warn_label, e)

    @staticmethod
    def save_theme_to_config(config: dict, theme_str: str):
        # 保存主题设置到配置文件
        # config: 配置字典
        # theme_str: 主题字符串（"light" 或 "dark"）
        # Save theme setting to config file
        # config: config dict
        # theme_str: theme string ("light" or "dark")
        AppController._update_and_save(config, "theme", theme_str, "主题")

    @staticmethod
    def save_floating_to_config(config: dict, floating_enabled: bool):
        # 保存悬浮窗设置到配置文件
        # config: 配置字典
        # floating_enabled: 悬浮窗是否启用
        # Save floating window setting to config file
        # config: config dict
        # floating_enabled: whether floating window is enabled
        AppController._update_and_save(config, "floating_enabled", floating_enabled, "悬浮窗")

    @staticmethod
    def save_toolbox_config(config: dict, key: str, value):
        # 保存工具箱配置项到配置文件
        # config: 配置字典
        # key: 配置键名
        # value: 配置值
        # Save toolbox config item to config file
        # config: config dict
        # key: config key name
        # value: config value
        AppController._update_and_save(config, key, value, "工具箱")

    @staticmethod
    def set_autostart_enabled(config: dict, enabled: bool):
        # 设置自启动并保存配置（整合配置更新+保存+注册三个步骤）
        # config: 配置字典
        # enabled: True=启用自启动，False=禁用自启动
        # Set auto-start and save config (integrate config update + save + register)
        # config: config dict
        # enabled: True=enable, False=disable
        # 保存配置到文件
        # Save config to file
        AppController._update_and_save(config, "autostart", enabled, "自启动")
        # 实际注册/取消注册开机启动（三级方案：注册表 > 快捷方式 > .bat）
        # Actually register/unregister auto-start (three-tier: registry > shortcut > .bat)
        AppController.set_autostart(enabled)

    @staticmethod
    def ensure_config_file(filename: str, default_content: str = ""):
        # 确保配置文件存在，不存在则创建，返回文件绝对路径
        # filename: 文件名（如 "hot.txt"）
        # default_content: 文件不存在时写入的默认内容
        # 返回: 文件绝对路径字符串
        # Ensure config file exists, create if not, return absolute path
        # filename: file name (e.g. "hot.txt")
        # default_content: default content to write if file doesn't exist
        # Returns: absolute file path string
        from pathlib import Path
        # 配置文件位于项目根目录的 config/ 子目录下
        # Config files are in config/ subdirectory of project root
        file_path = Path(__file__).parent.parent / "config" / filename
        # 文件不存在时创建
        # Create file if it doesn't exist
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(default_content, encoding="utf-8")
        # 返回字符串形式的绝对路径
        # Return absolute path as string
        return str(file_path)

    @staticmethod
    def change_language(config: dict, lang_code: str):
        # 切换语言并保存到配置文件
        # config: 配置字典
        # lang_code: 语言代码（如 "zh_CN"、"en_US"）
        # Change language and save to config file
        # config: config dict
        # lang_code: language code (e.g. "zh_CN", "en_US")
        AppController._update_and_save(config, 'language', lang_code, "语言")

    @staticmethod
    def load_history():
        # 加载历史记录（从 history.json 读取）
        # 返回: 历史记录列表，文件不存在时返回空列表
        # Load history (from history.json)
        # Returns: history list, empty list if file doesn't exist
        try:
            from .config import load_history
            return load_history()
        except Exception as e:
            logger.warning("加载历史记录失败: %s", e)
            return []

    @staticmethod
    def save_history_async(history: list):
        # 异步保存历史记录到文件（避免 IO 阻塞主线程导致界面卡顿）
        # 每次识别结果都会触发保存，必须异步
        # history: 要保存的历史记录列表
        # Async save history to file (avoid IO blocking main thread causing UI lag)
        # Triggered on every recognition result, must be async
        # history: history list to save
        # 制作快照（子线程读取，避免主线程同时修改）
        # Make snapshot (read by worker thread, avoid concurrent modification)
        history_snapshot = list(history)

        def _save_in_thread():
            # 子线程中执行文件写入
            # Execute file write in worker thread
            try:
                from .config import save_history
                save_history(history_snapshot)
            except Exception as e:
                logger.warning("保存历史记录失败: %s", e)

        # 启动守护线程（程序退出时自动结束）
        # Start daemon thread (auto-ends on program exit)
        threading.Thread(target=_save_in_thread, daemon=True).start()

    @staticmethod
    def clear_history():
        # 清空历史记录文件（删除 history.json）
        # Clear history file (delete history.json)
        try:
            from .config import clear_history
            clear_history()
        except Exception as e:
            logger.warning("清空历史记录失败: %s", e)

    @staticmethod
    def ensure_floating_default(config: dict):
        # 确保配置中包含 floating_enabled 字段，不存在则写入默认值 True 并保存
        # config: 配置字典
        # Ensure config contains floating_enabled field, write default True and save if missing
        # config: config dict
        if not config:
            return
        if "floating_enabled" not in config:
            AppController._update_and_save(config, "floating_enabled", True, "悬浮窗默认")

    @staticmethod
    def set_autostart(enabled: bool):
        # 设置或取消开机自启动
        # 三级方案：优先注册表 Run 键，失败回退快捷方式 .lnk，再失败回退 .bat
        # enabled: True=启用自启动，False=禁用自启动
        # Set or unset auto-start on boot
        # Three-tier: prefer registry Run key, fallback to shortcut .lnk, then .bat
        # enabled: True=enable auto-start, False=disable auto-start

        # 获取 Windows 启动目录路径
        # Get Windows Startup folder path
        startup_folder = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )
        # 快捷方式文件路径
        # Shortcut file path
        shortcut_path = os.path.join(startup_folder, "VoiceInput.lnk")

        if enabled:
            # ========== 启用自启动 ==========
            # 方案1：优先注册表 Run 键（主流方案，零依赖）
            # Tier 1: prefer registry Run key (mainstream, zero dependency)
            if registry_set_autostart(registry_get_command()):
                # 注册表成功，同时清理可能残留的旧快捷方式
                # Registry success, clean up any residual old shortcuts
                AppController._cleanup_shortcut(shortcut_path)
                return
            # 方案2：注册表失败，回退到快捷方式 .lnk
            # Tier 2: registry failed, fallback to shortcut .lnk
            logger.warning("开机启动: 注册表方案失败，回退到快捷方式")
            # 创建快捷方式
            # Create shortcut
            try:
                # 使用 win32com 创建快捷方式
                # Use win32com to create shortcut
                import pythoncom
                from win32com.shell import shell, shellcon
                # 初始化 COM
                # Initialize COM
                pythoncom.CoInitialize()
                # 创建 Shell 链接对象
                # Create Shell link object
                shortcut = pythoncom.CoCreateInstance(
                    shell.CLSID_ShellLink, None,
                    pythoncom.CLSCTX_INPROC_SERVER,
                    shell.IID_IShellLink
                )
                # 设置快捷方式目标路径
                # Set shortcut target path
                shortcut.SetPath(sys.executable)
                # 设置参数（运行模块）
                # Set arguments (run module)
                # 获取项目根目录
                # Get project root directory
                project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                shortcut.SetArguments(f'"{os.path.join(project_dir, "voiceinput", "__main__.py")}"')
                # 设置工作目录
                # Set working directory
                shortcut.SetWorkingDirectory(project_dir)
                # 设置描述
                # Set description
                shortcut.SetDescription("语音输入工具")
                # 保存快捷方式
                # Save shortcut
                persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
                persist.Save(shortcut_path, 0)
                logger.info("开机启动: 已创建快捷方式 '%s'", shortcut_path)
            except ImportError:
                # win32com 不可用，使用备用方案（直接创建 .bat 脚本）
                # win32com not available, use fallback (create .bat script)
                logger.warning("开机启动: win32com 不可用，使用备用方案")
                AppController._set_autostart_fallback(shortcut_path, True)
            except Exception as e:
                logger.error("开机启动: 创建快捷方式失败: %s", e)
        else:
            # ========== 禁用自启动 ==========
            # 删除所有方案的残留
            # Delete all residual from all tiers
            # 方案1：删除注册表 Run 键值
            # Tier 1: delete registry Run key value
            registry_remove_autostart()
            # 方案2：删除快捷方式
            # Tier 2: delete shortcut
            if os.path.exists(shortcut_path):
                try:
                    os.remove(shortcut_path)
                    logger.info("开机启动: 已删除快捷方式 '%s'", shortcut_path)
                except Exception as e:
                    logger.error("开机启动: 删除快捷方式失败: %s", e)
            # 方案3：删除 .bat 备用脚本
            # Tier 3: delete .bat fallback script
            bat_path = shortcut_path.replace(".lnk", ".bat")
            if os.path.exists(bat_path):
                try:
                    os.remove(bat_path)
                    logger.info("开机启动: 已删除启动脚本 '%s'", bat_path)
                except Exception as e:
                    logger.error("开机启动: 删除启动脚本失败: %s", e)

    @staticmethod
    def _cleanup_shortcut(shortcut_path: str):
        # 清理残留的快捷方式和 .bat 文件
        # shortcut_path: 快捷方式文件路径
        # Clean up residual shortcut and .bat files
        # shortcut_path: shortcut file path
        if os.path.exists(shortcut_path):
            try:
                os.remove(shortcut_path)
            except Exception:
                pass
        bat_path = shortcut_path.replace(".lnk", ".bat")
        if os.path.exists(bat_path):
            try:
                os.remove(bat_path)
            except Exception:
                pass

    @staticmethod
    def _set_autostart_fallback(shortcut_path: str, enabled: bool):
        # 备用方案：使用 .bat 文件替代快捷方式
        # shortcut_path: 快捷方式文件路径（用于推导 .bat 路径）
        # enabled: True=创建 .bat，False=删除 .bat
        # Fallback: use .bat file instead of shortcut
        # shortcut_path: shortcut file path (used to derive .bat path)
        # enabled: True=create .bat, False=delete .bat

        # 获取项目根目录
        # Get project root directory
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # bat 文件路径（与快捷方式同目录）
        # bat file path (same directory as shortcut)
        bat_path = shortcut_path.replace(".lnk", ".bat")
        if enabled:
            # 创建 bat 文件
            # Create bat file
            try:
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(f'@echo off\n')
                    f.write(f'cd /d "{project_dir}"\n')
                    f.write(f'"{sys.executable}" "{os.path.join(project_dir, "voiceinput", "__main__.py")}"\n')
                logger.info("开机启动: 已创建启动脚本 '%s'", bat_path)
            except Exception as e:
                logger.error("开机启动: 创建启动脚本失败: %s", e)
        else:
            # 删除 bat 文件
            # Delete bat file
            if os.path.exists(bat_path):
                try:
                    os.remove(bat_path)
                    logger.info("开机启动: 已删除启动脚本 '%s'", bat_path)
                except Exception as e:
                    logger.error("开机启动: 删除启动脚本失败: %s", e)
