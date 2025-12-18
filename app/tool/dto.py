"""
工具相关的数据传输对象（DTO）
用于API接口的数据传递
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ToolInfoDTO(BaseModel):
    """工具信息DTO"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters_schema: Dict[str, Any] = Field(..., description="工具参数JSON Schema")


class ToolListResponseDTO(BaseModel):
    """工具列表响应DTO"""
    tools: List[ToolInfoDTO] = Field(..., description="工具列表")
    count: int = Field(..., description="工具总数")


class ToolExecuteRequestDTO(BaseModel):
    """工具执行请求DTO"""
    tool_name: str = Field(..., description="要执行的工具名称")
    input: Dict[str, Any] = Field(..., description="工具输入参数")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="执行上下文（可选）")


class ToolExecuteResponseDTO(BaseModel):
    """工具执行响应DTO"""
    tool_name: str = Field(..., description="工具名称")
    result: Dict[str, Any] = Field(..., description="工具执行结果")
    success: bool = Field(True, description="是否执行成功")


class ToolOpenAISchemaDTO(BaseModel):
    """OpenAI格式的工具定义DTO（兼容Langdock）"""
    type: str = Field(default="function", description="工具类型")
    function: Dict[str, Any] = Field(..., description="函数定义")


class ToolListOpenAIResponseDTO(BaseModel):
    """OpenAI格式的工具列表响应DTO"""
    tools: List[Dict[str, Any]] = Field(..., description="工具列表（OpenAI格式）")
    count: int = Field(..., description="工具总数")

