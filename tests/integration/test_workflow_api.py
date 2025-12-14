"""
集成测试：工作流进度API端点
"""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.services.redis_service import RedisService, init_redis_service, close_redis_service
from app.configs.redis_config import RedisConfig
from main import create_app


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
async def app(redis_config):
    """Fixture for FastAPI app."""
    # 初始化Redis（必须在创建app之前）
    await init_redis_service(redis_config)
    
    # 验证Redis已初始化
    from app.services.redis_service import get_redis_service
    redis_service = get_redis_service()
    assert redis_service is not None, "Redis service should be initialized"
    assert redis_service.is_connected(), "Redis service should be connected"
    
    # 创建应用（注意：TestClient不会触发lifespan，所以Redis必须在之前初始化）
    app_instance = create_app()
    
    yield app_instance
    
    # 清理测试数据
    from app.services.redis_service import get_redis_service
    redis_service = get_redis_service()
    if redis_service and redis_service.client:
        keys = await redis_service.client.keys("workflow:progress:test_*")
        if keys:
            await redis_service.client.delete(*keys)
    
    # 清理日志处理器（关闭文件句柄）
    import logging
    root_logger = logging.getLogger()
    access_logger = logging.getLogger("access")
    
    # 关闭并移除所有文件处理器
    for handler in list(root_logger.handlers):
        if hasattr(handler, 'close'):
            handler.close()
        root_logger.removeHandler(handler)
    
    for handler in list(access_logger.handlers):
        if hasattr(handler, 'close'):
            handler.close()
        access_logger.removeHandler(handler)
    
    # 清理Redis
    await close_redis_service()


@pytest_asyncio.fixture
async def client(app):
    """Fixture for test client."""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflowAPI:
    """集成测试：工作流进度API"""

    async def test_create_workflow_progress(self, client):
        """测试创建工作流进度"""
        response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_1",
                "contract_id": "contract_123",
                "status": "processing",
                "progress": 50.0,
                "step_name": "审批中",
                "step_description": "等待部门经理审批",
                "metadata": {"approver": "张三"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "工作流进度创建成功"
        assert data["data"]["workflow_id"] == "test_workflow_1"
        assert data["data"]["contract_id"] == "contract_123"
        assert data["data"]["status"] == "processing"
        assert data["data"]["progress"] == 50.0
        assert data["data"]["step_name"] == "审批中"
        assert data["data"]["metadata"]["approver"] == "张三"

    async def test_create_workflow_progress_minimal(self, client):
        """测试使用最小字段创建工作流进度"""
        response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_2",
                "status": "pending",
                "progress": 0.0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["workflow_id"] == "test_workflow_2"
        assert data["data"]["status"] == "pending"
        assert data["data"]["progress"] == 0.0

    async def test_get_workflow_progress(self, client):
        """测试查询工作流进度"""
        # 先创建
        create_response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_3",
                "status": "processing",
                "progress": 75.0,
                "step_name": "审批中",
            },
        )
        assert create_response.status_code == 200

        # 查询
        response = await client.get("/api/v1/workflow/progress/test_workflow_3")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["workflow_id"] == "test_workflow_3"
        assert data["data"]["status"] == "processing"
        assert data["data"]["progress"] == 75.0
        assert data["data"]["step_name"] == "审批中"

    async def test_get_workflow_progress_not_found(self, client):
        """测试查询不存在的工作流进度"""
        response = await client.get("/api/v1/workflow/progress/non_existent_workflow")

        assert response.status_code == 404
        data = response.json()
        assert "工作流进度不存在" in data["detail"]

    async def test_update_workflow_progress(self, client):
        """测试更新工作流进度"""
        # 先创建
        create_response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_4",
                "status": "processing",
                "progress": 50.0,
                "step_name": "步骤1",
            },
        )
        assert create_response.status_code == 200

        # 更新
        response = await client.put(
            "/api/v1/workflow/progress/test_workflow_4",
            json={
                "status": "completed",
                "progress": 100.0,
                "step_name": "步骤2",
                "step_description": "已完成",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "工作流进度更新成功"
        assert data["data"]["status"] == "completed"
        assert data["data"]["progress"] == 100.0
        assert data["data"]["step_name"] == "步骤2"
        assert data["data"]["step_description"] == "已完成"

    async def test_update_workflow_progress_partial(self, client):
        """测试部分更新工作流进度"""
        # 先创建
        create_response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_5",
                "status": "processing",
                "progress": 50.0,
                "step_name": "步骤1",
            },
        )
        assert create_response.status_code == 200

        # 只更新状态
        response = await client.put(
            "/api/v1/workflow/progress/test_workflow_5",
            json={"status": "paused"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "paused"
        assert data["data"]["progress"] == 50.0  # 未改变
        assert data["data"]["step_name"] == "步骤1"  # 未改变

    async def test_update_workflow_progress_not_found(self, client):
        """测试更新不存在的工作流进度"""
        response = await client.put(
            "/api/v1/workflow/progress/non_existent_workflow",
            json={"status": "completed"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "工作流进度不存在" in data["detail"]

    async def test_delete_workflow_progress(self, client):
        """测试删除工作流进度"""
        # 先创建
        create_response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_6",
                "status": "processing",
                "progress": 50.0,
            },
        )
        assert create_response.status_code == 200

        # 删除
        response = await client.delete("/api/v1/workflow/progress/test_workflow_6")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "工作流进度删除成功"
        assert data["data"] is True

        # 验证已删除
        get_response = await client.get("/api/v1/workflow/progress/test_workflow_6")
        assert get_response.status_code == 404

    async def test_delete_workflow_progress_not_found(self, client):
        """测试删除不存在的工作流进度"""
        response = await client.delete("/api/v1/workflow/progress/non_existent_workflow")

        assert response.status_code == 404
        data = response.json()
        assert "工作流进度不存在" in data["detail"]

    async def test_create_workflow_progress_validation_error(self, client):
        """测试创建工作流进度 - 验证错误"""
        # 进度值超出范围
        response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_7",
                "status": "processing",
                "progress": 150.0,  # 超出100
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_update_workflow_progress_metadata_merge(self, client):
        """测试更新时metadata合并"""
        # 先创建
        create_response = await client.post(
            "/api/v1/workflow/progress",
            json={
                "workflow_id": "test_workflow_8",
                "status": "processing",
                "progress": 50.0,
                "metadata": {"key1": "value1", "key2": "value2"},
            },
        )
        assert create_response.status_code == 200

        # 更新metadata
        response = await client.put(
            "/api/v1/workflow/progress/test_workflow_8",
            json={"metadata": {"key2": "new_value2", "key3": "value3"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["metadata"] == {
            "key1": "value1",
            "key2": "new_value2",
            "key3": "value3",
        }

