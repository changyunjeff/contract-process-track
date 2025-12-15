"""
工作流进度实体

领域实体，包含业务逻辑和不变性约束
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.tools import current_timestamp_ms


class WorkflowProgress(BaseModel):
    """
    工作流进度实体
    
    领域实体，表示工作流执行过程中的进度状态
    """
    workflow_id: str = Field(..., description="工作流唯一标识符")
    contract_id: Optional[str] = Field(None, description="合同ID")
    status: str = Field(..., description="当前工作流状态")
    progress: float = Field(..., description="进度百分比（0-100）")
    step_name: Optional[str] = Field(None, description="当前步骤名称")
    step_description: Optional[str] = Field(None, description="当前步骤描述")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外的元数据信息")
    created_at: int = Field(..., description="创建时间")
    updated_at: int = Field(..., description="更新时间")

    @field_validator("progress")
    @classmethod
    def validate_progress(cls, v: float) -> float:
        """验证进度值在有效范围内"""
        if not 0.0 <= v <= 100.0:
            raise ValueError("进度值必须在0-100之间")
        return v

    def update_progress(
        self,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        step_name: Optional[str] = None,
        step_description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        更新工作流进度
        
        领域方法，封装业务逻辑
        """
        if status is not None:
            self.status = status
        if progress is not None:
            self.progress = progress
        if step_name is not None:
            self.step_name = step_name
        if step_description is not None:
            self.step_description = step_description
        if metadata is not None:
            # 合并metadata
            if self.metadata:
                self.metadata.update(metadata)
            else:
                self.metadata = metadata
        
        self.updated_at = current_timestamp_ms()

    def is_completed(self) -> bool:
        """检查工作流是否已完成"""
        return self.progress >= 100.0

    def is_failed(self) -> bool:
        """检查工作流是否失败"""
        return self.status.lower() in ["failed", "error", "exception"]

