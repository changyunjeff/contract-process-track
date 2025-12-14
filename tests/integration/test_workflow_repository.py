"""
集成测试：工作流进度Redis仓储
"""
import os
import pytest
import pytest_asyncio
from datetime import datetime
from app.domains.workflow.domain.entities import WorkflowProgress
from app.domains.workflow.infrastructure.repositories import RedisWorkflowProgressRepository
from app.services.redis_service import RedisService, init_redis_service, close_redis_service
from app.configs.redis_config import RedisConfig


@pytest.fixture
def redis_config():
    """Fixture for Redis configuration."""
    return RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )


@pytest_asyncio.fixture
async def redis_service(redis_config):
    """Fixture for Redis service."""
    service = RedisService(redis_config)
    try:
        await service.connect()
        yield service
    finally:
        await service.disconnect()


@pytest_asyncio.fixture
async def workflow_repository(redis_config):
    """Fixture for workflow repository."""
    # 初始化全局Redis服务（RedisWorkflowProgressRepository使用全局服务）
    await init_redis_service(redis_config)
    
    try:
        repository = RedisWorkflowProgressRepository()
        yield repository
    finally:
        # 清理测试数据
        from app.services.redis_service import get_redis_service
        redis_service = get_redis_service()
        if redis_service and redis_service.client:
            keys = await redis_service.client.keys("workflow:progress:test_*")
            if keys:
                await redis_service.client.delete(*keys)
        
        # 关闭全局Redis服务
        await close_redis_service()


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisWorkflowProgressRepository:
    """集成测试：Redis工作流进度仓储"""

    async def test_create_progress(self, workflow_repository):
        """测试创建工作流进度"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        now = datetime.utcnow()
        workflow_progress = WorkflowProgress(
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

        # 创建
        created = await workflow_repository.create(workflow_progress)

        # 验证
        assert created.workflow_id == "test_workflow_1"
        assert created.contract_id == "contract_123"
        assert created.status == "processing"
        assert created.progress == 50.0

        # 验证已保存到Redis
        retrieved = await workflow_repository.get_by_workflow_id("test_workflow_1")
        assert retrieved is not None
        assert retrieved.workflow_id == "test_workflow_1"
        assert retrieved.contract_id == "contract_123"
        assert retrieved.status == "processing"
        assert retrieved.progress == 50.0
        assert retrieved.metadata == {"approver": "张三"}

    async def test_get_by_workflow_id_not_found(self, workflow_repository):
        """测试查询不存在的工作流进度"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        result = await workflow_repository.get_by_workflow_id("non_existent_workflow")
        assert result is None

    async def test_update_progress(self, workflow_repository):
        """测试更新工作流进度"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        # 创建初始进度
        now = datetime.utcnow()
        initial = WorkflowProgress(
            workflow_id="test_workflow_2",
            status="processing",
            progress=50.0,
            step_name="步骤1",
            created_at=now,
            updated_at=now,
        )
        await workflow_repository.create(initial)

        # 更新进度
        initial.update_progress(
            status="completed",
            progress=100.0,
            step_name="步骤2",
            step_description="已完成",
        )
        updated = await workflow_repository.update(initial)

        # 验证
        assert updated.status == "completed"
        assert updated.progress == 100.0
        assert updated.step_name == "步骤2"
        assert updated.step_description == "已完成"
        assert updated.updated_at > now

        # 验证已更新到Redis
        retrieved = await workflow_repository.get_by_workflow_id("test_workflow_2")
        assert retrieved.status == "completed"
        assert retrieved.progress == 100.0

    async def test_delete_progress(self, workflow_repository):
        """测试删除工作流进度"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        # 创建进度
        now = datetime.utcnow()
        workflow_progress = WorkflowProgress(
            workflow_id="test_workflow_3",
            status="processing",
            progress=50.0,
            created_at=now,
            updated_at=now,
        )
        await workflow_repository.create(workflow_progress)

        # 验证存在
        retrieved = await workflow_repository.get_by_workflow_id("test_workflow_3")
        assert retrieved is not None

        # 删除
        result = await workflow_repository.delete("test_workflow_3")
        assert result is True

        # 验证已删除
        retrieved = await workflow_repository.get_by_workflow_id("test_workflow_3")
        assert retrieved is None

    async def test_delete_progress_not_found(self, workflow_repository):
        """测试删除不存在的工作流进度"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        result = await workflow_repository.delete("non_existent_workflow")
        assert result is False

    async def test_create_and_retrieve_with_metadata(self, workflow_repository):
        """测试创建和查询包含metadata的工作流进度"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        now = datetime.utcnow()
        workflow_progress = WorkflowProgress(
            workflow_id="test_workflow_4",
            status="processing",
            progress=50.0,
            metadata={
                "approver": "张三",
                "department": "技术部",
                "priority": "high",
            },
            created_at=now,
            updated_at=now,
        )

        await workflow_repository.create(workflow_progress)

        retrieved = await workflow_repository.get_by_workflow_id("test_workflow_4")
        assert retrieved is not None
        assert retrieved.metadata == {
            "approver": "张三",
            "department": "技术部",
            "priority": "high",
        }

    async def test_update_progress_metadata_merge(self, workflow_repository):
        """测试更新时metadata合并"""
        if not workflow_repository.redis_service or not workflow_repository.redis_service.is_connected():
            pytest.skip("Redis not connected")

        # 创建初始进度
        now = datetime.utcnow()
        initial = WorkflowProgress(
            workflow_id="test_workflow_5",
            status="processing",
            progress=50.0,
            metadata={"key1": "value1", "key2": "value2"},
            created_at=now,
            updated_at=now,
        )
        await workflow_repository.create(initial)

        # 更新metadata
        initial.update_progress(metadata={"key2": "new_value2", "key3": "value3"})
        await workflow_repository.update(initial)

        # 验证metadata被合并
        retrieved = await workflow_repository.get_by_workflow_id("test_workflow_5")
        assert retrieved.metadata == {
            "key1": "value1",
            "key2": "new_value2",
            "key3": "value3",
        }

    async def test_redis_unavailable(self, redis_config):
        """测试Redis不可用时的错误处理"""
        # 使用无效配置创建仓储
        invalid_config = RedisConfig(host="invalid_host", port=6379)
        service = RedisService(invalid_config)
        repository = RedisWorkflowProgressRepository()
        repository.redis_service = service

        now = datetime.utcnow()
        workflow_progress = WorkflowProgress(
            workflow_id="test_workflow_6",
            status="processing",
            progress=50.0,
            created_at=now,
            updated_at=now,
        )

        # 应该抛出RuntimeError
        with pytest.raises(RuntimeError, match="Redis service is not available"):
            await repository.create(workflow_progress)

