from PIL import Image
import pytesseract
from typing import Dict, Any
from .base import ToolInterface


class OCRParserTool(ToolInterface):
    name = "ocr_parser"
    description = "OCR image-based contract parser. Extracts text from images using OCR technology."

    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取OCR工具的JSON Schema定义"""
        return {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file to be processed"
                },
                "lang": {
                    "type": "string",
                    "description": "OCR language code (default: chi_sim for simplified Chinese)",
                    "default": "chi_sim",
                    "enum": ["chi_sim", "chi_tra", "eng", "jpn", "kor"]
                }
            },
            "required": ["image_path"]
        }

    def run(self, input: dict, context: dict) -> dict:
        """
        执行OCR解析
        
        Args:
            input: 包含image_path和可选lang的字典
            context: 执行上下文
            
        Returns:
            dict: 包含提取文本的结果
        """
        image_path = input.get("image_path")
        if not image_path:
            raise ValueError("image_path is required")
        
        lang = input.get("lang", "chi_sim")
        
        try:
            img = Image.open(f"/data/files/{image_path}")
            text = pytesseract.image_to_string(img, lang=lang)
            return {
                "type": "text",
                "source": image_path,
                "content": text.strip(),
                "lang": lang
            }
        except Exception as e:
            return {
                "type": "error",
                "source": image_path,
                "error": str(e)
            }


