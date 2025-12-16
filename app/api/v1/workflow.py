"""
工作流进度API路由（v1版本）

表现层，处理HTTP请求和响应
"""
from __future__ import annotations

from fastapi import APIRouter

from app.models import HttpResponse
from app.exceptions import ServerUnavailableException, InternalServerException
from app.domains.workflow.application.services import WorkflowProgressApplicationService
from app.domains.workflow.application.dto import (
    WorkflowProgressCreateDTO,
    WorkflowProgressUpdateDTO,
    WorkflowProgressDTO,
)
from app.domains.workflow.infrastructure.repositories import RedisWorkflowProgressRepository

workflow_router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])


def get_application_service() -> WorkflowProgressApplicationService:
    """获取应用服务实例（依赖注入）"""
    from app.services.redis_service import get_redis_service
    redis_service = get_redis_service()
    if not redis_service or not redis_service.is_connected():
        raise RuntimeError("Redis service is not available")
    repository = RedisWorkflowProgressRepository()
    return WorkflowProgressApplicationService(repository)


@workflow_router.post("/progress", response_model=HttpResponse[WorkflowProgressDTO])
async def create_workflow_progress(
    data: WorkflowProgressCreateDTO
) -> HttpResponse[WorkflowProgressDTO]:
    """
    创建工作流进度追踪

    用于记录n8n或langgraph工作流执行过程中的状态进度。
    """
    try:
        service = get_application_service()
        progress = await service.create_progress(data)
        return HttpResponse.success(data=progress, msg="工作流进度创建成功")
    except RuntimeError as e:
        raise ServerUnavailableException(f"Redis服务不可用: {str(e)}")
    except Exception as e:
        raise InternalServerException(f"创建工作流进度失败: {str(e)}")


@workflow_router.put(
    "/progress/{workflow_id}",
    response_model=HttpResponse[WorkflowProgressDTO]
)
async def update_workflow_progress(
    workflow_id: str,
    data: WorkflowProgressUpdateDTO
) -> HttpResponse[WorkflowProgressDTO]:
    """
    更新工作流进度追踪

    用于更新已存在的工作流进度信息。
    """
    try:
        service = get_application_service()
        progress = await service.update_progress(workflow_id, data)
        if progress is None:
            raise NotFoundException(f"工作流进度不存在: {workflow_id}")
        return HttpResponse.success(data=progress, msg="工作流进度更新成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"Redis服务不可用: {str(e)}")
    except Exception as e:
        raise InternalServerException(f"更新工作流进度失败: {str(e)}")


@workflow_router.get(
    "/progress/{workflow_id}",
    response_model=HttpResponse[WorkflowProgressDTO]
)
async def get_workflow_progress(workflow_id: str) -> HttpResponse[WorkflowProgressDTO]:
    """
    查询工作流进度追踪

    根据工作流ID查询当前的工作流状态进度。
    """
    try:
        service = get_application_service()
        progress = await service.get_progress(workflow_id)
        if progress is None:
            raise NotFoundException(f"工作流进度不存在: {workflow_id}")
        return HttpResponse.success(data=progress, msg="查询成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"Redis服务不可用: {str(e)}")
    except Exception as e:
        raise InternalServerException(f"查询工作流进度失败: {str(e)}")


@workflow_router.delete("/progress/{workflow_id}", response_model=HttpResponse[bool])
async def delete_workflow_progress(workflow_id: str) -> HttpResponse[bool]:
    """
    删除工作流进度追踪

    删除指定的工作流进度记录。
    """
    try:
        service = get_application_service()
        deleted = await service.delete_progress(workflow_id)
        if not deleted:
            raise NotFoundException(f"工作流进度不存在: {workflow_id}")
        return HttpResponse.success(data=True, msg="工作流进度删除成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"Redis服务不可用: {str(e)}")
    except Exception as e:
        raise InternalServerException(f"删除工作流进度失败: {str(e)}")

