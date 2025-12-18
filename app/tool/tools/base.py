from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, create_model


class ToolParameter(BaseModel):
    """工具参数定义"""
    type: str = Field(..., description="参数类型: string, number, integer, boolean, array, object")
    description: Optional[str] = Field(None, description="参数描述")
    enum: Optional[list] = Field(None, description="枚举值列表")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(True, description="是否必需")


class ToolInterface(ABC):
    """工具接口基类"""
    name: str
    description: str

    @abstractmethod
    def run(self, input: dict, context: dict) -> dict:
        """
        执行工具
        
        Args:
            input: 工具输入参数
            context: 执行上下文（可选，用于传递额外信息）
            
        Returns:
            dict: 工具执行结果
        """
        pass

    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取工具参数的JSON Schema定义
        
        Returns:
            Dict: JSON Schema格式的参数定义
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def to_openai_schema(self) -> Dict[str, Any]:
        """
        转换为OpenAI Function Calling格式（兼容Langdock）
        
        Returns:
            Dict: OpenAI格式的工具定义
        """
        parameters_schema = self.get_parameters_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters_schema
            }
        }
