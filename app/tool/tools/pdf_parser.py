"""
PDF 文件解析工具
用于将 PDF 文件解析为纯文本
"""
from typing import Dict, Any
from .base import ToolInterface

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    try:
        import PyPDF2
        PYPDF2_AVAILABLE = True
    except ImportError:
        PYPDF2_AVAILABLE = False


class PdfParserTool(ToolInterface):
    name = "pdf_parser"
    description = "Parse PDF files and extract text content. Supports extracting text from PDF documents, including tables and structured content."

    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取PDF解析工具的JSON Schema定义"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the PDF file to be parsed"
                },
                "extract_tables": {
                    "type": "boolean",
                    "description": "Whether to extract table content from PDF (default: true). Only works with pdfplumber library.",
                    "default": True
                },
                "page_range": {
                    "type": "string",
                    "description": "Page range to extract (e.g., '1-5', '1,3,5', 'all'). Default is 'all' to extract all pages.",
                    "default": "all"
                },
                "extract_images": {
                    "type": "boolean",
                    "description": "Whether to extract image metadata (default: false). Note: actual image extraction requires additional processing.",
                    "default": False
                }
            },
            "required": ["file_path"]
        }

    def _parse_page_range(self, page_range: str, total_pages: int) -> list:
        """
        解析页面范围字符串
        
        Args:
            page_range: 页面范围字符串，如 '1-5', '1,3,5', 'all'
            total_pages: 总页数
            
        Returns:
            list: 页面索引列表（从0开始）
        """
        if page_range.lower() == "all":
            return list(range(total_pages))
        
        pages = []
        parts = page_range.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 范围，如 '1-5'
                start, end = part.split('-', 1)
                start = int(start.strip()) - 1  # 转换为0-based索引
                end = int(end.strip())  # 保持1-based，用于range
                pages.extend(range(start, end))
            else:
                # 单个页面
                page_num = int(part.strip()) - 1  # 转换为0-based索引
                pages.append(page_num)
        
        # 去重并排序，过滤无效页面
        pages = sorted(set([p for p in pages if 0 <= p < total_pages]))
        return pages

    def _extract_text_with_pdfplumber(self, file_path: str, extract_tables: bool, page_range: str) -> Dict[str, Any]:
        """使用 pdfplumber 提取文本"""
        import pdfplumber
        
        all_text_parts = []
        tables_text = []
        total_pages = 0
        
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = self._parse_page_range(page_range, total_pages)
            
            for page_idx in pages_to_extract:
                page = pdf.pages[page_idx]
                
                # 提取页面文本
                page_text = page.extract_text()
                if page_text:
                    all_text_parts.append(f"[Page {page_idx + 1}]\n{page_text.strip()}")
                
                # 提取表格（如果需要）
                if extract_tables:
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables):
                            table_rows = []
                            for row in table:
                                if row:  # 过滤空行
                                    row_cells = [str(cell) if cell is not None else "" for cell in row]
                                    table_rows.append(" | ".join(row_cells))
                            if table_rows:
                                tables_text.append(f"[Page {page_idx + 1}, Table {table_idx + 1}]\n" + "\n".join(table_rows))
        
        # 组合文本
        full_text = "\n\n".join(all_text_parts)
        if tables_text:
            full_text += "\n\n[Tables]\n" + "\n\n".join(tables_text)
        
        return {
            "text": full_text,
            "total_pages": total_pages,
            "extracted_pages": len(pages_to_extract),
            "table_count": len(tables_text) if extract_tables else 0
        }

    def _extract_text_with_pypdf2(self, file_path: str, page_range: str) -> Dict[str, Any]:
        """使用 PyPDF2 提取文本（回退方案）"""
        import PyPDF2
        
        all_text_parts = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            pages_to_extract = self._parse_page_range(page_range, total_pages)
            
            for page_idx in pages_to_extract:
                page = pdf_reader.pages[page_idx]
                page_text = page.extract_text()
                if page_text:
                    all_text_parts.append(f"[Page {page_idx + 1}]\n{page_text.strip()}")
        
        full_text = "\n\n".join(all_text_parts)
        
        return {
            "text": full_text,
            "total_pages": total_pages,
            "extracted_pages": len(pages_to_extract),
            "table_count": 0  # PyPDF2 不支持表格提取
        }

    def run(self, input: dict, context: dict) -> dict:
        """
        执行PDF文件解析
        
        Args:
            input: 包含file_path和可选参数的字典
            context: 执行上下文
            
        Returns:
            dict: 包含提取文本的结果
        """
        if not PDFPLUMBER_AVAILABLE and not PYPDF2_AVAILABLE:
            return {
                "type": "error",
                "error": "PDF parsing libraries are not installed. Please install one of: pip install pdfplumber (recommended) or pip install PyPDF2"
            }
        
        file_path = input.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")
        
        extract_tables = input.get("extract_tables", True)
        page_range = input.get("page_range", "all")
        extract_images = input.get("extract_images", False)
        
        # 如果路径不是绝对路径，则使用基础路径（与其他工具保持一致）
        import os
        if not os.path.isabs(file_path):
            base_path = "/data/files"
            full_path = os.path.join(base_path, file_path)
        else:
            full_path = file_path
        
        try:
            # 优先使用 pdfplumber（功能更强大）
            if PDFPLUMBER_AVAILABLE:
                result = self._extract_text_with_pdfplumber(full_path, extract_tables, page_range)
            else:
                # 回退到 PyPDF2
                if extract_tables:
                    return {
                        "type": "error",
                        "source": file_path,
                        "error": "Table extraction requires pdfplumber library. Please install: pip install pdfplumber"
                    }
                result = self._extract_text_with_pypdf2(full_path, page_range)
            
            full_text = result["text"]
            
            # 统计信息
            stats = {
                "total_pages": result["total_pages"],
                "extracted_pages": result["extracted_pages"],
                "table_count": result["table_count"],
                "total_characters": len(full_text),
                "total_words": len(full_text.split()) if full_text else 0,
                "library_used": "pdfplumber" if PDFPLUMBER_AVAILABLE else "PyPDF2"
            }
            
            # 图像元数据（如果请求）
            image_info = None
            if extract_images and PDFPLUMBER_AVAILABLE:
                try:
                    import pdfplumber
                    with pdfplumber.open(full_path) as pdf:
                        image_count = 0
                        for page in pdf.pages:
                            images = page.images
                            image_count += len(images) if images else 0
                        if image_count > 0:
                            image_info = {
                                "total_images": image_count,
                                "note": "Image metadata only. Actual image extraction requires additional processing."
                            }
                except Exception:
                    pass  # 忽略图像提取错误
            
            response = {
                "type": "text",
                "source": file_path,
                "content": full_text,
                "stats": stats,
                "extract_tables": extract_tables,
                "page_range": page_range
            }
            
            if image_info:
                response["image_info"] = image_info
            
            return response
            
        except FileNotFoundError:
            return {
                "type": "error",
                "source": file_path,
                "error": f"File not found: {full_path}"
            }
        except Exception as e:
            return {
                "type": "error",
                "source": file_path,
                "error": f"Failed to parse PDF file: {str(e)}"
            }

