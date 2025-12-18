"""
Redis工作流进度仓储实现

基础设施层实现，负责与Redis交互
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from ..domain.entities import WorkflowProgress
from ..domain.repositories import IWorkflowProgressRepository
from app.services.redis_service import get_redis_service
from app.common import datetime_to_timestamp_ms

logger = logging.getLogger(__name__)

# Redis key前缀
WORKFLOW_KEY_PREFIX = "workflow:progress:"


class RedisWorkflowProgressRepository(IWorkflowProgressRepository):
    """基于Redis的工作流进度仓储实现"""

    def __init__(self):
        """初始化Redis仓储"""
        self.redis_service = get_redis_service()

    def _get_redis_key(self, workflow_id: str) -> str:
        """生成Redis key"""
        return f"{WORKFLOW_KEY_PREFIX}{workflow_id}"

    def _check_redis_available(self) -> None:
        """检查Redis是否可用"""
        if not self.redis_service or not self.redis_service.is_connected():
            raise RuntimeError("Redis service is not available")
        
        if self.redis_service.client is None:
            raise RuntimeError("Redis client is not available")

    async def create(self, workflow_progress: WorkflowProgress) -> WorkflowProgress:
        """创建工作流进度"""
        self._check_redis_available()
        
        redis_key = self._get_redis_key(workflow_progress.workflow_id)
        redis_client = self.redis_service.client

        # 序列化为JSON存储
        progress_dict = workflow_progress.model_dump(mode="json")
        # 将datetime转换为ISO格式字符串
        progress_dict["created_at"] = workflow_progress.created_at.isoformat()
        progress_dict["updated_at"] = workflow_progress.updated_at.isoformat()

        await redis_client.set(redis_key, json.dumps(progress_dict))

        logger.info(f"Created workflow progress in Redis: {workflow_progress.workflow_id}")
        return workflow_progress

    async def update(self, workflow_progress: WorkflowProgress) -> WorkflowProgress:
        """更新工作流进度"""
        self._check_redis_available()
        
        redis_key = self._get_redis_key(workflow_progress.workflow_id)
        redis_client = self.redis_service.client

        # 序列化为JSON存储
        progress_dict = workflow_progress.model_dump(mode="json")
        progress_dict["created_at"] = workflow_progress.created_at.isoformat()
        progress_dict["updated_at"] = workflow_progress.updated_at.isoformat()

        await redis_client.set(redis_key, json.dumps(progress_dict))

        logger.info(f"Updated workflow progress in Redis: {workflow_progress.workflow_id}")
        return workflow_progress

    async def get_by_workflow_id(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """根据工作流ID查询工作流进度"""
        self._check_redis_available()
        
        redis_key = self._get_redis_key(workflow_id)
        redis_client = self.redis_service.client

        # 从Redis获取数据
        data = await redis_client.get(redis_key)
        if not data:
            return None

        # 解析数据
        progress_dict = json.loads(data)
        return WorkflowProgress(
            workflow_id=progress_dict["workflow_id"],
            contract_id=progress_dict.get("contract_id"),
            status=progress_dict["status"],
            progress=progress_dict["progress"],
            step_name=progress_dict.get("step_name"),
            step_description=progress_dict.get("step_description"),
            metadata=progress_dict.get("metadata"),
            created_at=datetime_to_timestamp_ms(datetime.fromisoformat(progress_dict["created_at"])),
            updated_at=datetime_to_timestamp_ms(datetime.fromisoformat(progress_dict["updated_at"])),
        )

    async def delete(self, workflow_id: str) -> bool:
        """删除工作流进度"""
        self._check_redis_available()
        
        redis_key = self._get_redis_key(workflow_id)
        redis_client = self.redis_service.client

        result = await redis_client.delete(redis_key)
        logger.info(f"Deleted workflow progress from Redis: {workflow_id}")
        return result > 0

