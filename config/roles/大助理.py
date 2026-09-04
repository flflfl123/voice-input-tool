# -*- coding: utf-8 -*-
# 大助理角色定义文件
# Big assistant role definition file

# 角色名称
# Role name
name = "大助理"

# 触发关键词列表
# Trigger keyword list
trigger_words = ["大助理"]

# 系统提示词
# System prompt
system_prompt = """你是一个智能大助理，拥有广泛的知识和出色的推理能力。
请根据用户的输入提供详细、准确、有帮助的回答。
直接输出回复内容，不要添加任何前缀或解释。"""

# 输出模式：typing=打字输出，toast=弹窗输出
# Output mode: typing=typing output, toast=toast output
output_mode = "typing"

# 是否启用对话历史
# Whether to enable conversation history
enable_history = True

# 最大上下文轮数
# Max context rounds
max_context = 20
