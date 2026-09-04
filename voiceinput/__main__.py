# -*- coding: utf-8 -*-
# 语音输入工具 - 命令行入口
# Voice Input Tool - command line entry point
# 支持通过 python -m voiceinput 方式启动程序
# Supports launching via python -m voiceinput

# 导入系统相关功能库
# Import system-related functionality
import sys
# 导入路径处理库
# Import path processing library
from pathlib import Path

# ========== 路径配置 ==========
# ========== Path Configuration ==========
# 获取当前文件所在目录的父目录（项目根目录）
# Get the parent directory of the current file (project root directory)
# resolve()确保获取绝对路径
# resolve() ensures getting absolute path
parent_dir = str(Path(__file__).resolve().parent.parent)
# 检查父目录是否已在系统路径中
# Check if parent directory is already in system path
if parent_dir not in sys.path:
    # 将父目录插入系统路径的开头，确保优先查找
    # Insert parent directory at the beginning of system path for priority lookup
    sys.path.insert(0, parent_dir)

# 从voiceinput.main模块导入主函数
# Import main function from voiceinput.main module
from voiceinput.main import main

# ========== 程序入口点 ==========
# ========== Program Entry Point ==========
# 当直接运行此文件时调用主函数
# Call main function when running this file directly
if __name__ == "__main__":
    # 调用主函数启动程序
    # Call main function to start the program
    main()
