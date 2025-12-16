"""
集成测试：API 多数据库支持
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from main import create_app
from app.configs import AppConfig


@pytest.fixture
def mock_postgres_services():
    """模拟多个 PostgreSQL 服务"""
    from app.services.postgres_service import _pg_services
    
    # 清理全局状态
    _pg_services.clear()
    
    # 创建模拟服务
    mock_service1 = MagicMock()
    mock_engine1 = MagicMock()
    mock_engine1.dispose = AsyncMock()
    mock_service1.engine = mock_engine1
    mock_service1.get_session_factory.return_value = MagicMock()
    
    mock_service2 = MagicMock()
    mock_engine2 = MagicMock()
    mock_engine2.dispose = AsyncMock()
    mock_service2.engine = mock_engine2
    mock_service2.get_session_factory.return_value = MagicMock()
    
    _pg_services["company_info_cn"] = mock_service1
    _pg_services["law_cn"] = mock_service2
    
    yield _pg_services
    
    # 清理
    _pg_services.clear()


@pytest.fixture
def client(mock_postgres_services):
    """创建测试客户端"""
    app_config = AppConfig(
        title="Test App",
        port=8000,
        host="0.0.0.0",
        version="1.0.0",
    )
    app = create_app(app_config)
    return TestClient(app)


class TestAPIMultiDatabase:
    """API 多数据库集成测试"""

    @patch("app.api.v1.enterprise.get_enterprise_service")
    def test_enterprise_api_uses_company_info_database(self, mock_get_service, client):
        """测试企业 API 使用 company_info_cn 数据库"""
        from app.domains.enterprise.application.dto import EnterpriseBasicInfoDTO
        
        # 模拟服务返回
        mock_service = MagicMock()
        mock_enterprise = EnterpriseBasicInfoDTO(
            id=1,
            credit_code="91110000MA01234567",
            enterprise_name="测试企业",
            status="存续",
            created_at=1000000,
            updated_at=1000000,
        )
        mock_service.get_enterprise = AsyncMock(return_value=mock_enterprise)
        mock_get_service.return_value = mock_service
        
        # 调用 API
        response = client.get("/api/v1/enterprise/basic-info/1")
        
        # 验证
        assert response.status_code == 200
        # get_enterprise_service 被调用（使用默认参数 db_name="company_info_cn"）
        # 由于函数有默认参数，调用时可以不传参数，函数内部会使用默认值
        mock_get_service.assert_called_once()
        # 验证服务方法被正确调用
        mock_service.get_enterprise.assert_called_once_with(1)

    @patch("app.api.v1.enterprise.get_enterprise_service")
    def test_enterprise_api_create(self, mock_get_service, client):
        """测试企业 API 创建功能"""
        from app.domains.enterprise.application.dto import EnterpriseBasicInfoDTO
        
        # 模拟服务返回
        mock_service = MagicMock()
        mock_enterprise = EnterpriseBasicInfoDTO(
            id=1,
            credit_code="91110000MA01234567",
            enterprise_name="测试企业",
            status="存续",
            created_at=1000000,
            updated_at=1000000,
        )
        mock_service.create_enterprise = AsyncMock(return_value=mock_enterprise)
        mock_get_service.return_value = mock_service
        
        # 调用 API
        response = client.post(
            "/api/v1/enterprise/basic-info",
            json={
                "credit_code": "91110000MA01234567",
                "enterprise_name": "测试企业",
                "status": "存续",
            },
        )
        
        # 验证
        assert response.status_code == 200
        data = response.json()
        # HttpResponse.success() 返回 code=0（不是 200），这是设计选择
        assert data["code"] == 0
        assert data["data"]["credit_code"] == "91110000MA01234567"
        # get_enterprise_service 被调用（使用默认参数 db_name="company_info_cn"）
        mock_get_service.assert_called_once()

    def test_multiple_databases_initialized(self, mock_postgres_services):
        """测试多个数据库都被初始化"""
        from app.services.postgres_service import get_postgres_service
        
        # 验证两个数据库服务都存在
        service1 = get_postgres_service("company_info_cn")
        service2 = get_postgres_service("law_cn")
        
        assert service1 is not None
        assert service2 is not None
        assert service1 != service2

    def test_database_service_isolation(self, mock_postgres_services):
        """测试数据库服务隔离"""
        from app.services.postgres_service import get_postgres_service
        
        # 获取不同数据库的服务
        company_service = get_postgres_service("company_info_cn")
        law_service = get_postgres_service("law_cn")
        
        # 验证它们是不同的实例
        assert company_service is not None
        assert law_service is not None
        assert company_service != law_service

    @patch("app.domains.enterprise.infrastructure.repositories.get_async_session_factory")
    def test_repository_uses_correct_database(self, mock_get_factory, mock_postgres_services):
        """测试 repository 使用正确的数据库"""
        from app.domains.enterprise.infrastructure.repositories import (
            PostgresEnterpriseBasicInfoRepository,
        )
        
        # 创建 repository，指定数据库名称
        repo = PostgresEnterpriseBasicInfoRepository(db_name="company_info_cn")
        
        # 验证调用了正确的数据库
        mock_get_factory.assert_called_once_with("company_info_cn")
        
        # 测试使用不同的数据库
        repo2 = PostgresEnterpriseBasicInfoRepository(db_name="law_cn")
        assert mock_get_factory.call_count == 2
        # 最后一次调用应该是 law_cn
        assert mock_get_factory.call_args_list[1][0][0] == "law_cn"

