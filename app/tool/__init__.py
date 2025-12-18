"""
工具模块
提供工具注册和管理功能
"""
from .registry import tool_registry, ToolRegistry
from .tools.base import ToolInterface
from .tools import _all_tools


# 自动注册所有工具
def _auto_register_tools():
    """自动注册所有工具"""
    for tool in _all_tools:
        tool_registry.register(tool)

# 在模块导入时自动注册工具
_auto_register_tools()

__all__ = [
    "ToolRegistry",
    "ToolInterface",
    "tool_registry",
]
