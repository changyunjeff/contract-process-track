"""
工具模块
导出所有可用的工具
"""
from .ocr_parser import OCRParserTool
from .docx_parser import DocxParserTool
from .pdf_parser import PdfParserTool

# 所有可用工具的列表
__all__ = [
    "OCRParserTool",
    "DocxParserTool",
    "PdfParserTool",
]

# 自动发现并导出所有工具实例
_all_tools = [
    OCRParserTool(),
    DocxParserTool(),
    PdfParserTool(),
]
