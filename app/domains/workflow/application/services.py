"""
工作流进度应用服务

应用层服务，协调领域对象和仓储，实现业务用例
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from ..domain.entities import WorkflowProgress
from ..domain.repositories import IWorkflowProgressRepository
from .dto import WorkflowProgressCreateDTO, WorkflowProgressUpdateDTO, WorkflowProgressDTO

logger = logging.getLogger(__name__)


class WorkflowProgressApplicationService:
    """工作流进度应用服务"""

    def __init__(self, repository: IWorkflowProgressRepository):
        """
        初始化应用服务
        
        Args:
            repository: 工作流进度仓储
        """
        self.repository = repository

    async def create_progress(self, dto: WorkflowProgressCreateDTO) -> WorkflowProgressDTO:
        """
        创建工作流进度
        
        Args:
            dto: 创建工作流进度的DTO
            
        Returns:
            WorkflowProgressDTO: 创建的工作流进度DTO
        """
        now = datetime.utcnow()
        
        # 创建领域实体
        workflow_progress = WorkflowProgress(
            workflow_id=dto.workflow_id,
            contract_id=dto.contract_id,
            status=dto.status,
            progress=dto.progress,
            step_name=dto.step_name,
            step_description=dto.step_description,
            metadata=dto.metadata,
            created_at=now,
            updated_at=now,
        )
        
        # 通过仓储保存
        created = await self.repository.create(workflow_progress)
        
        logger.info(f"Created workflow progress: {dto.workflow_id}")
        
        # 转换为DTO返回
        return self._entity_to_dto(created)

    async def update_progress(
        self, workflow_id: str, dto: WorkflowProgressUpdateDTO
    ) -> Optional[WorkflowProgressDTO]:
        """
        更新工作流进度
        
        Args:
            workflow_id: 工作流ID
            dto: 更新工作流进度的DTO
            
        Returns:
            Optional[WorkflowProgressDTO]: 更新后的工作流进度DTO，如果不存在则返回None
        """
        # 查询现有实体
        existing = await self.repository.get_by_workflow_id(workflow_id)
        if not existing:
            return None
        
        # 使用领域方法更新
        existing.update_progress(
            status=dto.status,
            progress=dto.progress,
            step_name=dto.step_name,
            step_description=dto.step_description,
            metadata=dto.metadata,
        )
        
        # 通过仓储保存
        updated = await self.repository.update(existing)
        
        logger.info(f"Updated workflow progress: {workflow_id}")
        
        # 转换为DTO返回
        return self._entity_to_dto(updated)

    async def get_progress(self, workflow_id: str) -> Optional[WorkflowProgressDTO]:
        """
        查询工作流进度
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[WorkflowProgressDTO]: 工作流进度DTO，如果不存在则返回None
        """
        workflow_progress = await self.repository.get_by_workflow_id(workflow_id)
        if not workflow_progress:
            return None
        
        return self._entity_to_dto(workflow_progress)

    async def delete_progress(self, workflow_id: str) -> bool:
        """
        删除工作流进度
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            bool: 是否删除成功
        """
        result = await self.repository.delete(workflow_id)
        logger.info(f"Deleted workflow progress: {workflow_id}")
        return result

    def _entity_to_dto(self, entity: WorkflowProgress) -> WorkflowProgressDTO:
        """将领域实体转换为DTO"""
        return WorkflowProgressDTO(
            workflow_id=entity.workflow_id,
            contract_id=entity.contract_id,
            status=entity.status,
            progress=entity.progress,
            step_name=entity.step_name,
            step_description=entity.step_description,
            metadata=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

