"""
数据传输对象（DTO）

应用层的数据传输对象，用于API接口和领域实体之间的转换
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkflowProgressCreateDTO(BaseModel):
    """创建工作流进度的DTO"""
    workflow_id: str = Field(..., description="工作流唯一标识符")
    contract_id: Optional[str] = Field(None, description="合同ID（可选）")
    status: str = Field(..., description="当前工作流状态")
    progress: float = Field(..., ge=0.0, le=100.0, description="进度百分比（0-100）")
    step_name: Optional[str] = Field(None, description="当前步骤名称")
    step_description: Optional[str] = Field(None, description="当前步骤描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外的元数据信息")


class WorkflowProgressUpdateDTO(BaseModel):
    """更新工作流进度的DTO"""
    status: Optional[str] = Field(None, description="当前工作流状态")
    progress: Optional[float] = Field(None, ge=0.0, le=100.0, description="进度百分比（0-100）")
    step_name: Optional[str] = Field(None, description="当前步骤名称")
    step_description: Optional[str] = Field(None, description="当前步骤描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外的元数据信息")


class WorkflowProgressDTO(BaseModel):
    """工作流进度的DTO"""
    workflow_id: str = Field(..., description="工作流唯一标识符")
    contract_id: Optional[str] = Field(None, description="合同ID")
    status: str = Field(..., description="当前工作流状态")
    progress: float = Field(..., description="进度百分比（0-100）")
    step_name: Optional[str] = Field(None, description="当前步骤名称")
    step_description: Optional[str] = Field(None, description="当前步骤描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外的元数据信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

