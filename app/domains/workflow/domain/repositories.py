"""
工作流进度仓储接口

定义领域层需要的仓储接口，由基础设施层实现
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import WorkflowProgress


class IWorkflowProgressRepository(ABC):
    """工作流进度仓储接口"""

    @abstractmethod
    async def create(self, workflow_progress: WorkflowProgress) -> WorkflowProgress:
        """
        创建工作流进度
        
        Args:
            workflow_progress: 工作流进度实体
            
        Returns:
            WorkflowProgress: 创建的工作流进度实体
        """
        pass

    @abstractmethod
    async def update(self, workflow_progress: WorkflowProgress) -> WorkflowProgress:
        """
        更新工作流进度
        
        Args:
            workflow_progress: 工作流进度实体
            
        Returns:
            WorkflowProgress: 更新后的工作流进度实体
        """
        pass

    @abstractmethod
    async def get_by_workflow_id(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """
        根据工作流ID查询工作流进度
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[WorkflowProgress]: 工作流进度实体，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def delete(self, workflow_id: str) -> bool:
        """
        删除工作流进度
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否删除成功
        """
        pass

