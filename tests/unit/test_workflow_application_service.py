"""
单元测试：工作流进度应用服务
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from app.domains.workflow.application.services import WorkflowProgressApplicationService
from app.domains.workflow.application.dto import (
    WorkflowProgressCreateDTO,
    WorkflowProgressUpdateDTO,
)
from app.domains.workflow.domain.entities import WorkflowProgress


@pytest.mark.unit
class TestWorkflowProgressApplicationService:
    """测试工作流进度应用服务"""

    @pytest.fixture
    def mock_repository(self):
        """创建模拟仓储"""
        return MagicMock()

    @pytest.fixture
    def application_service(self, mock_repository):
        """创建应用服务实例"""
        return WorkflowProgressApplicationService(mock_repository)

    @pytest.mark.asyncio
    async def test_create_progress(self, application_service, mock_repository):
        """测试创建工作流进度"""
        # 准备数据
        create_dto = WorkflowProgressCreateDTO(
            workflow_id="test_workflow_1",
            contract_id="contract_123",
            status="processing",
            progress=50.0,
            step_name="审批中",
            step_description="等待部门经理审批",
            metadata={"approver": "张三"},
        )

        # 模拟仓储返回
        created_entity = WorkflowProgress(
            workflow_id="test_workflow_1",
            contract_id="contract_123",
            status="processing",
            progress=50.0,
            step_name="审批中",
            step_description="等待部门经理审批",
            metadata={"approver": "张三"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_repository.create = AsyncMock(return_value=created_entity)

        # 执行
        result = await application_service.create_progress(create_dto)

        # 验证
        assert result.workflow_id == "test_workflow_1"
        assert result.contract_id == "contract_123"
        assert result.status == "processing"
        assert result.progress == 50.0
        assert result.step_name == "审批中"
        assert result.step_description == "等待部门经理审批"
        assert result.metadata == {"approver": "张三"}
        mock_repository.create.assert_called_once()
        # 验证传递给仓储的实体
        call_args = mock_repository.create.call_args[0][0]
        assert call_args.workflow_id == "test_workflow_1"
        assert call_args.status == "processing"

    @pytest.mark.asyncio
    async def test_update_progress_success(self, application_service, mock_repository):
        """测试更新工作流进度 - 成功"""
        # 准备数据
        workflow_id = "test_workflow_2"
        update_dto = WorkflowProgressUpdateDTO(
            status="completed",
            progress=100.0,
            step_name="已完成",
        )

        # 模拟现有实体
        existing_entity = WorkflowProgress(
            workflow_id=workflow_id,
            status="processing",
            progress=50.0,
            step_name="审批中",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # 模拟仓储方法
        mock_repository.get_by_workflow_id = AsyncMock(return_value=existing_entity)
        mock_repository.update = AsyncMock(return_value=existing_entity)

        # 执行
        result = await application_service.update_progress(workflow_id, update_dto)

        # 验证
        assert result is not None
        assert result.status == "completed"
        assert result.progress == 100.0
        assert result.step_name == "已完成"
        mock_repository.get_by_workflow_id.assert_called_once_with(workflow_id)
        mock_repository.update.assert_called_once()
        # 验证实体被更新
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.status == "completed"
        assert updated_entity.progress == 100.0

    @pytest.mark.asyncio
    async def test_update_progress_not_found(self, application_service, mock_repository):
        """测试更新工作流进度 - 不存在"""
        # 准备数据
        workflow_id = "test_workflow_3"
        update_dto = WorkflowProgressUpdateDTO(status="completed")

        # 模拟仓储返回None
        mock_repository.get_by_workflow_id = AsyncMock(return_value=None)

        # 执行
        result = await application_service.update_progress(workflow_id, update_dto)

        # 验证
        assert result is None
        mock_repository.get_by_workflow_id.assert_called_once_with(workflow_id)
        mock_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_progress_success(self, application_service, mock_repository):
        """测试查询工作流进度 - 成功"""
        # 准备数据
        workflow_id = "test_workflow_4"

        # 模拟实体
        entity = WorkflowProgress(
            workflow_id=workflow_id,
            status="processing",
            progress=75.0,
            step_name="审批中",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # 模拟仓储
        mock_repository.get_by_workflow_id = AsyncMock(return_value=entity)

        # 执行
        result = await application_service.get_progress(workflow_id)

        # 验证
        assert result is not None
        assert result.workflow_id == workflow_id
        assert result.status == "processing"
        assert result.progress == 75.0
        mock_repository.get_by_workflow_id.assert_called_once_with(workflow_id)

    @pytest.mark.asyncio
    async def test_get_progress_not_found(self, application_service, mock_repository):
        """测试查询工作流进度 - 不存在"""
        # 准备数据
        workflow_id = "test_workflow_5"

        # 模拟仓储返回None
        mock_repository.get_by_workflow_id = AsyncMock(return_value=None)

        # 执行
        result = await application_service.get_progress(workflow_id)

        # 验证
        assert result is None
        mock_repository.get_by_workflow_id.assert_called_once_with(workflow_id)

    @pytest.mark.asyncio
    async def test_delete_progress_success(self, application_service, mock_repository):
        """测试删除工作流进度 - 成功"""
        # 准备数据
        workflow_id = "test_workflow_6"

        # 模拟仓储
        mock_repository.delete = AsyncMock(return_value=True)

        # 执行
        result = await application_service.delete_progress(workflow_id)

        # 验证
        assert result is True
        mock_repository.delete.assert_called_once_with(workflow_id)

    @pytest.mark.asyncio
    async def test_delete_progress_failed(self, application_service, mock_repository):
        """测试删除工作流进度 - 失败"""
        # 准备数据
        workflow_id = "test_workflow_7"

        # 模拟仓储返回False
        mock_repository.delete = AsyncMock(return_value=False)

        # 执行
        result = await application_service.delete_progress(workflow_id)

        # 验证
        assert result is False
        mock_repository.delete.assert_called_once_with(workflow_id)

    @pytest.mark.asyncio
    async def test_update_progress_metadata_merge(self, application_service, mock_repository):
        """测试更新metadata时合并"""
        # 准备数据
        workflow_id = "test_workflow_8"
        update_dto = WorkflowProgressUpdateDTO(
            metadata={"key2": "new_value2", "key3": "value3"}
        )

        # 模拟现有实体（已有metadata）
        existing_entity = WorkflowProgress(
            workflow_id=workflow_id,
            status="processing",
            progress=50.0,
            metadata={"key1": "value1", "key2": "value2"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        mock_repository.get_by_workflow_id = AsyncMock(return_value=existing_entity)
        mock_repository.update = AsyncMock(return_value=existing_entity)

        # 执行
        result = await application_service.update_progress(workflow_id, update_dto)

        # 验证metadata被合并
        updated_entity = mock_repository.update.call_args[0][0]
        assert updated_entity.metadata == {
            "key1": "value1",
            "key2": "new_value2",
            "key3": "value3",
        }

