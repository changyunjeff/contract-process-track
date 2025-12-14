"""
单元测试：工作流进度领域实体
"""
import pytest
from datetime import datetime
from app.domains.workflow.domain.entities import WorkflowProgress


@pytest.mark.unit
class TestWorkflowProgress:
    """测试工作流进度实体"""

    def test_create_workflow_progress(self):
        """测试创建工作流进度实体"""
        now = datetime.utcnow()
        progress = WorkflowProgress(
            workflow_id="test_workflow_1",
            contract_id="contract_123",
            status="processing",
            progress=50.0,
            step_name="审批中",
            step_description="等待部门经理审批",
            metadata={"approver": "张三"},
            created_at=now,
            updated_at=now,
        )

        assert progress.workflow_id == "test_workflow_1"
        assert progress.contract_id == "contract_123"
        assert progress.status == "processing"
        assert progress.progress == 50.0
        assert progress.step_name == "审批中"
        assert progress.step_description == "等待部门经理审批"
        assert progress.metadata == {"approver": "张三"}
        assert progress.created_at == now
        assert progress.updated_at == now

    def test_create_workflow_progress_minimal(self):
        """测试使用最小字段创建工作流进度"""
        now = datetime.utcnow()
        progress = WorkflowProgress(
            workflow_id="test_workflow_2",
            status="pending",
            progress=0.0,
            created_at=now,
            updated_at=now,
        )

        assert progress.workflow_id == "test_workflow_2"
        assert progress.contract_id is None
        assert progress.status == "pending"
        assert progress.progress == 0.0
        assert progress.step_name is None
        assert progress.step_description is None
        assert progress.metadata is None

    def test_progress_validation_valid(self):
        """测试进度值验证 - 有效值"""
        now = datetime.utcnow()
        # 应该不抛出异常
        progress = WorkflowProgress(
            workflow_id="test_workflow_3",
            status="processing",
            progress=75.5,
            created_at=now,
            updated_at=now,
        )
        assert progress.progress == 75.5

    def test_progress_validation_boundary(self):
        """测试进度值验证 - 边界值"""
        now = datetime.utcnow()
        # 最小值
        progress_min = WorkflowProgress(
            workflow_id="test_workflow_4",
            status="pending",
            progress=0.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_min.progress == 0.0

        # 最大值
        progress_max = WorkflowProgress(
            workflow_id="test_workflow_5",
            status="completed",
            progress=100.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_max.progress == 100.0

    def test_progress_validation_invalid(self):
        """测试进度值验证 - 无效值"""
        now = datetime.utcnow()
        # 小于0
        with pytest.raises(ValueError, match="进度值必须在0-100之间"):
            WorkflowProgress(
                workflow_id="test_workflow_6",
                status="error",
                progress=-1.0,
                created_at=now,
                updated_at=now,
            )

        # 大于100
        with pytest.raises(ValueError, match="进度值必须在0-100之间"):
            WorkflowProgress(
                workflow_id="test_workflow_7",
                status="error",
                progress=101.0,
                created_at=now,
                updated_at=now,
            )

    def test_update_progress(self):
        """测试更新工作流进度"""
        now = datetime.utcnow()
        progress = WorkflowProgress(
            workflow_id="test_workflow_8",
            status="processing",
            progress=50.0,
            step_name="步骤1",
            created_at=now,
            updated_at=now,
        )

        # 更新进度
        progress.update_progress(
            status="completed",
            progress=100.0,
            step_name="步骤2",
            step_description="已完成",
        )

        assert progress.status == "completed"
        assert progress.progress == 100.0
        assert progress.step_name == "步骤2"
        assert progress.step_description == "已完成"
        assert progress.updated_at > now

    def test_update_progress_partial(self):
        """测试部分更新工作流进度"""
        now = datetime.utcnow()
        progress = WorkflowProgress(
            workflow_id="test_workflow_9",
            status="processing",
            progress=50.0,
            step_name="步骤1",
            created_at=now,
            updated_at=now,
        )

        # 只更新状态
        progress.update_progress(status="paused")

        assert progress.status == "paused"
        assert progress.progress == 50.0  # 未改变
        assert progress.step_name == "步骤1"  # 未改变

    def test_update_progress_metadata_merge(self):
        """测试更新metadata时合并"""
        now = datetime.utcnow()
        progress = WorkflowProgress(
            workflow_id="test_workflow_10",
            status="processing",
            progress=50.0,
            metadata={"key1": "value1", "key2": "value2"},
            created_at=now,
            updated_at=now,
        )

        # 更新metadata，应该合并
        progress.update_progress(metadata={"key2": "new_value2", "key3": "value3"})

        assert progress.metadata == {
            "key1": "value1",
            "key2": "new_value2",
            "key3": "value3",
        }

    def test_update_progress_metadata_new(self):
        """测试更新metadata时新建"""
        now = datetime.utcnow()
        progress = WorkflowProgress(
            workflow_id="test_workflow_11",
            status="processing",
            progress=50.0,
            created_at=now,
            updated_at=now,
        )

        # 更新metadata，应该新建
        progress.update_progress(metadata={"key1": "value1"})

        assert progress.metadata == {"key1": "value1"}

    def test_is_completed(self):
        """测试检查工作流是否完成"""
        now = datetime.utcnow()
        # 未完成
        progress_incomplete = WorkflowProgress(
            workflow_id="test_workflow_12",
            status="processing",
            progress=50.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_incomplete.is_completed() is False

        # 完成
        progress_complete = WorkflowProgress(
            workflow_id="test_workflow_13",
            status="completed",
            progress=100.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_complete.is_completed() is True

        # 超过100也算完成
        progress_over = WorkflowProgress(
            workflow_id="test_workflow_14",
            status="completed",
            progress=100.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_over.is_completed() is True

    def test_is_failed(self):
        """测试检查工作流是否失败"""
        now = datetime.utcnow()
        # 失败状态
        progress_failed = WorkflowProgress(
            workflow_id="test_workflow_15",
            status="failed",
            progress=30.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_failed.is_failed() is True

        # 错误状态
        progress_error = WorkflowProgress(
            workflow_id="test_workflow_16",
            status="error",
            progress=30.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_error.is_failed() is True

        # 异常状态
        progress_exception = WorkflowProgress(
            workflow_id="test_workflow_17",
            status="exception",
            progress=30.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_exception.is_failed() is True

        # 正常状态
        progress_normal = WorkflowProgress(
            workflow_id="test_workflow_18",
            status="processing",
            progress=50.0,
            created_at=now,
            updated_at=now,
        )
        assert progress_normal.is_failed() is False

