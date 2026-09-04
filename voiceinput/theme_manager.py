# -*- coding: utf-8 -*-
# 主题管理模块 - 负责主题颜色和字体管理
# 从 gui.py 抽取的纯数据/逻辑模块，无 GUI 依赖
# 可被 gui.py 和 gui2.py（PySide6 版本）共同调用
# Theme manager module - responsible for theme colors and font management
# Pure data/logic module extracted from gui.py, no GUI dependencies
# Can be shared by gui.py and gui2.py (PySide6 version)

# 导入日志记录库
# Import logging library
import logging

# 从 i18n 模块导入获取当前界面语言的函数
# Import function to get current UI language from i18n module
from .i18n import get_current_language

# 创建本模块的日志记录器
# Create logger for this module
logger = logging.getLogger("VoiceInput")


# ========== 主题模式常量定义 ==========
# ========== Theme mode constants ==========
# 亮色模式标识
THEME_LIGHT = 0
# 暗色模式标识
THEME_DARK = 1


# ========== 全局字体定义 ==========
# ========== Global font definitions ==========
# 根据界面语言动态返回最合适的字体
# 必须在运行时调用（不能在模块加载时调用），以确保获取正确的语言设置
#
# 字体映射表：语言代码 -> 首选字体列表（按优先级排序）
# 所有字体均为 Windows 系统自带字体（Win10+），100% 可用，无需额外检查
_FONT_MAP = {
    "zh_CN": ["Microsoft YaHei", "SimHei", "SimSun"],     # 简体中文：微软雅黑优先
    "zh_TW": ["Microsoft YaHei", "MingLiU", "SimSun"],    # 繁体中文：微软雅黑优先
    "ja": ["Yu Gothic", "MS Gothic", "Meiryo"],            # 日文：游ゴシック优先
    "ko": ["Malgun Gothic", "Gulim", "Batang"],            # 韩文：맑은 고딕优先
}
# 其他语言的默认字体列表（按优先级排序）
# Segoe UI 是 Windows 系统的标准 UI 字体
_DEFAULT_FONTS = ["Segoe UI", "Tahoma", "Arial"]

# 全局字体缓存，避免每次调用都重复计算
# Global font cache, avoid repeated calculation
_font_cache = {}

# 全局字体缩放系数（1.0=不缩放，由 config.font_scale 传入）
# Global font scale factor (1.0=no scaling, set from config.font_scale)
_font_scale = 1.0


def set_font_scale(scale: float):
    # 设置全局字体缩放系数（启动时由 gui.py 从 config 读取后调用）
    # 限制范围 0.8-1.5，防止异常值
    # Set global font scale factor (called by gui.py on startup from config)
    # Clamped to 0.8-1.5 to prevent abnormal values
    global _font_scale
    _font_scale = max(0.8, min(1.5, float(scale)))


def get_font_size(base: int) -> int:
    # 根据全局字体缩放系数计算实际字体大小
    # base: 基准字体大小（如 15）
    # 返回: 缩放后的字体大小，最小 8（避免太小看不见）
    # Calculate actual font size based on global font scale factor
    # base: base font size (e.g. 15)
    # Returns: scaled font size, min 8 (avoid too small to see)
    return max(8, int(round(base * _font_scale)))


def get_font_family():
    # 获取当前界面语言对应的最佳可用字体
    # 返回字体家族名称（字符串）
    # 按优先级依次返回，第一个字体为首选，后续为回退字体
    # Get the best available font for the current UI language
    # Returns font family name (string)
    # Returns by priority, first font is preferred, rest are fallbacks

    # 获取当前界面语言代码
    lang = get_current_language()

    # 使用缓存避免重复计算
    # Use cache to avoid repeated calculation
    if lang in _font_cache:
        return _font_cache[lang]

    # 获取当前语言的字体候选列表，未匹配则用默认字体
    # Get font candidates for current language, use default if no match
    font_candidates = _FONT_MAP.get(lang, _DEFAULT_FONTS)

    # 返回第一个字体（首选字体）
    # 注：所有候选字体均为 Windows 系统自带，实际使用时 tkinter/Qt 会自动回退
    # Return first font (preferred)
    # Note: all candidate fonts are Windows built-in, tkinter/Qt auto-fallbacks
    result = font_candidates[0]
    _font_cache[lang] = result
    return result


class ThemeColors:
    # 主题颜色管理类
    # 负责管理亮色和暗色主题的颜色配置，统一从 config.json 读取
    # 纯数据类，不依赖任何 GUI 库，可被 CustomTkinter 和 PySide6 共同使用
    # Theme color manager class
    # Manages light and dark theme colors, reads from config.json
    # Pure data class, no GUI dependency, usable by both CustomTkinter and PySide6

    def __init__(self, config=None):
        # 初始化主题颜色
        # config: 配置字典，包含 theme_colors 字段
        # Initialize theme colors
        # config: config dict containing theme_colors field

        # 默认使用暗色模式
        self.dark_mode = True
        # 保存配置引用
        self._config = config
        # 应用暗色主题（默认）
        self.apply_dark()

    def apply_dark(self):
        # 应用暗色主题，统一从 config.json 读取颜色
        # 默认值参考 Material Design 暗色模式
        # Apply dark theme, read colors from config.json
        # Default values follow Material Design dark mode

        # 如果配置中存在暗色主题颜色，则从配置读取
        if self._config and "theme_colors" in self._config and "dark" in self._config["theme_colors"]:
            colors = self._config["theme_colors"]["dark"]
            # 主背景色（最深）
            self.bg = colors.get("bg", "#1E1E1E")
            # 侧边栏背景色
            self.sidebar = colors.get("sidebar", "#252525")
            # 内容区背景色
            self.content = colors.get("content", "#2D2D2D")
            # 卡片背景色（最浅）
            self.card = colors.get("card", "#383838")
            # 主文字颜色
            self.text = colors.get("text", "#E0E0E0")
            # 次要文字颜色
            self.text_secondary = colors.get("text_secondary", "#A0A0A0")
            # 悬停背景色
            self.hover = colors.get("hover", "#3A3A3A")
            # 激活背景色
            self.active = colors.get("active", "#404040")
            # 强调色（按钮、链接等）
            self.accent = colors.get("accent", "#4A90D9")
            # 边框色
            self.border = colors.get("border", "#444444")
            # Logo 颜色
            self.logo_color = colors.get("logo_color", "#FFFFFF")
            # 危险色（删除按钮等）
            self.danger = colors.get("danger", "#D9534F")
            # 危险色悬停
            self.danger_hover = colors.get("danger_hover", "#C9302C")
        else:
            # 配置不存在时使用默认暗色值
            self.bg = "#1E1E1E"
            self.sidebar = "#252525"
            self.content = "#2D2D2D"
            self.card = "#383838"
            self.text = "#E0E0E0"
            self.text_secondary = "#A0A0A0"
            self.hover = "#3A3A3A"
            self.active = "#404040"
            self.accent = "#4A90D9"
            self.border = "#444444"
            self.logo_color = "#FFFFFF"
            self.danger = "#D9534F"
            self.danger_hover = "#C9302C"
        # 标记当前为暗色模式
        self.dark_mode = True

    def apply_light(self):
        # 应用亮色主题，统一从 config.json 读取颜色
        # 默认值参考 WPF/Material Design 亮色模式，层次分明
        # bg(深) > sidebar > content > card(浅)
        # Apply light theme, read colors from config.json
        # Default values follow WPF/Material Design light mode, clear hierarchy

        # 如果配置中存在亮色主题颜色，则从配置读取
        if self._config and "theme_colors" in self._config and "light" in self._config["theme_colors"]:
            colors = self._config["theme_colors"]["light"]
            # 主背景色（柔和暖灰，避免纯白刺眼又不过于灰暗）
            self.bg = colors.get("bg", "#F5F5F0")
            # 侧边栏背景色（稍深，区分层次）
            self.sidebar = colors.get("sidebar", "#EBEBE6")
            # 内容区背景色（与主背景接近，微区分）
            self.content = colors.get("content", "#FAFAF8")
            # 卡片背景色（纯白，与内容区形成对比）
            self.card = colors.get("card", "#FFFFFF")
            # 主文字颜色（深灰）
            self.text = colors.get("text", "#333333")
            # 次要文字颜色
            self.text_secondary = colors.get("text_secondary", "#666666")
            # 悬停背景色
            self.hover = colors.get("hover", "#E8E8E3")
            # 激活背景色
            self.active = colors.get("active", "#D8D8D3")
            # 强调色（按钮、链接等）
            self.accent = colors.get("accent", "#4A90D9")
            # 边框色（浅灰，柔和不突兀）
            self.border = colors.get("border", "#CCCCCC")
            # Logo 颜色
            self.logo_color = colors.get("logo_color", "#000000")
            # 危险色（删除按钮等）
            self.danger = colors.get("danger", "#D9534F")
            # 危险色悬停
            self.danger_hover = colors.get("danger_hover", "#C9302C")
        else:
            # 配置不存在时使用默认亮色值（柔和暖灰，非纯白）
            self.bg = "#F5F5F0"
            self.sidebar = "#EBEBE6"
            self.content = "#FAFAF8"
            self.card = "#FFFFFF"
            self.text = "#333333"
            self.text_secondary = "#666666"
            self.hover = "#E8E8E3"
            self.active = "#D8D8D3"
            self.accent = "#4A90D9"
            self.border = "#CCCCCC"
            self.logo_color = "#000000"
            self.danger = "#D9534F"
            self.danger_hover = "#C9302C"
        # 标记当前为亮色模式
        self.dark_mode = False
