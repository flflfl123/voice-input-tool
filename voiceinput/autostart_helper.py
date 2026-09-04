# -*- coding: utf-8 -*-
# 开机自启动辅助模块 - 使用注册表 Run 键实现
# 主流小工具（Everything、Snipaste、Ditto）常用方案
# 用 Python 标准库 winreg，零第三方依赖
# Auto-start helper module - uses registry Run key
# Common approach for mainstream tools (Everything, Snipaste, Ditto)
# Uses Python standard library winreg, zero third-party dependencies

# 导入日志记录库
# Import logging library
import logging
# 导入Windows注册表操作库（标准库）
# Import Windows registry operation library (standard library)
import winreg

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")

# ========== 注册表 Run 键路径 ==========
# ========== Registry Run key path ==========
# 当前用户的启动项注册表路径
# Current user's startup registry path
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
# 注册表值名称
# Registry value name
_APP_NAME = "VoiceInput"


def set_autostart(command: str) -> bool:
    # 设置开机自启动（写入注册表 Run 键）
    # command: 启动命令，格式为 "python.exe路径" "脚本路径"
    # 返回 True 表示成功，False 表示失败
    # Set auto-start on boot (write to registry Run key)
    # command: startup command, format "python.exe path" "script path"
    # Return True if successful, False if failed

    try:
        # 打开当前用户的 Run 键（可写）
        # Open current user's Run key (writable)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,   # 当前用户根键 / Current user root key
            _RUN_KEY,                   # Run 键路径 / Run key path
            0,                          # 保留参数 / Reserved parameter
            winreg.KEY_SET_VALUE        # 可写权限 / Write permission
        )
        # 写入注册表值（字符串类型）
        # Write registry value (string type)
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, command)
        # 关闭注册表键
        # Close registry key
        winreg.CloseKey(key)
        # 记录成功日志
        # Log success
        logger.info("自启动: 已写入注册表 Run 键: %s", command)
        return True
    except PermissionError as e:
        # 权限不足（罕见，HKEY_CURRENT_USER 通常无需管理员权限）
        # 调用方会回退到快捷方式方案
        # Permission denied (rare, HKEY_CURRENT_USER usually doesn't need admin)
        # Caller will fall back to shortcut approach
        logger.warning("自启动: 注册表写入权限不足，将回退快捷方式: %s", e)
        return False
    except OSError as e:
        # 注册表操作系统级错误（键不存在、访问被拒等）
        # OS-level registry error (key not found, access denied, etc.)
        logger.warning("自启动: 注册表写入系统错误: %s", e)
        return False
    except Exception as e:
        # 其他未知异常
        # Other unknown exceptions
        logger.error("自启动: 写入注册表失败: %s", e)
        return False


def remove_autostart() -> bool:
    # 移除开机自启动（删除注册表 Run 键中的值）
    # 返回 True 表示成功，False 表示失败
    # Remove auto-start on boot (delete value from registry Run key)
    # Return True if successful, False if failed

    try:
        # 打开当前用户的 Run 键（可写）
        # Open current user's Run key (writable)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,   # 当前用户根键 / Current user root key
            _RUN_KEY,                   # Run 键路径 / Run key path
            0,                          # 保留参数 / Reserved parameter
            winreg.KEY_SET_VALUE        # 可写权限 / Write permission
        )
        try:
            # 删除注册表值
            # Delete registry value
            winreg.DeleteValue(key, _APP_NAME)
            logger.info("自启动: 已从注册表删除 Run 键值")
        except FileNotFoundError:
            # 值不存在，说明本来就没注册，不算错误
            # Value doesn't exist, means not registered, not an error
            logger.debug("自启动: 注册表中无 Run 键值，无需删除")
        # 关闭注册表键
        # Close registry key
        winreg.CloseKey(key)
        return True
    except Exception as e:
        # 记录失败日志
        # Log failure
        logger.error("自启动: 删除注册表值失败: %s", e)
        return False


def is_registered() -> bool:
    # 检查是否已注册开机自启动
    # 返回 True 表示已注册，False 表示未注册
    # Check if auto-start is registered
    # Return True if registered, False if not

    try:
        # 打开当前用户的 Run 键（只读）
        # Open current user's Run key (read-only)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,   # 当前用户根键 / Current user root key
            _RUN_KEY,                   # Run 键路径 / Run key path
            0,                          # 保留参数 / Reserved parameter
            winreg.KEY_READ             # 只读权限 / Read permission
        )
        try:
            # 尝试读取值
            # Try to read value
            winreg.QueryValueEx(key, _APP_NAME)
            # 读取成功，说明已注册
            # Read successful, means registered
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            # 值不存在，说明未注册
            # Value doesn't exist, means not registered
            winreg.CloseKey(key)
            return False
    except Exception as e:
        # 记录异常日志
        # Log exception
        logger.debug("自启动: 检查注册表失败: %s", e)
        return False


def get_command() -> str:
    # 构建启动命令字符串
    # 格式: "python.exe路径" "脚本路径"
    # 返回启动命令字符串
    # Build startup command string
    # Format: "python.exe path" "script path"
    # Return startup command string

    # 导入系统库（获取 Python 解释器路径）
    # Import system library (get Python interpreter path)
    import sys
    # 导入路径处理库
    # Import path processing library
    import os
    # 获取项目根目录（voiceinput 的父目录）
    # Get project root directory (parent of voiceinput)
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # 主脚本路径
    # Main script path
    main_script = os.path.join(project_dir, "voiceinput", "__main__.py")
    # 构建启动命令（路径用引号包裹，防止路径含空格）
    # Build startup command (paths wrapped in quotes to handle spaces)
    command = f'"{sys.executable}" "{main_script}"'
    return command
