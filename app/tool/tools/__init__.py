"""
工具模块
导出所有可用的工具
"""
from .ocr_parser import OCRParserTool

# 所有可用工具的列表
__all__ = [
    "OCRParserTool",
]

# 自动发现并导出所有工具实例
_all_tools = [
    OCRParserTool(),
]
