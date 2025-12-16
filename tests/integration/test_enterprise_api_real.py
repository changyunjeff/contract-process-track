"""
真实 API 集成测试：测试运行中的服务器

这些测试直接调用 http://localhost:8512 上的实际 API 端点
确保服务器已启动：python main.py 或 uvicorn main:app --host 0.0.0.0 --port 8512
"""
from __future__ import annotations

import pytest
import httpx
from datetime import date
from typing import Dict, Any
import time


# 测试服务器地址
BASE_URL = "http://localhost:8512"


@pytest.fixture
def client():
    """创建 HTTP 客户端"""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.fixture
def test_enterprise_data() -> Dict[str, Any]:
    """测试用的企业数据"""
    # 使用时间戳确保唯一性
    timestamp = int(time.time() * 1000)
    return {
        "credit_code": f"91110000MA{timestamp:010d}"[-18:],  # 确保18位
        "enterprise_name": f"测试企业_{timestamp}",
        "status": "存续",
        "legal_representative": "张三",
        "registered_capital": "1000万元",
        "establishment_date": "2020-01-01",
        "enterprise_type": "有限责任公司",
        "registration_authority": "北京市市场监督管理局",
        "registered_address": "北京市朝阳区测试街道123号",
    }


@pytest.fixture
def test_enterprise_data_minimal() -> Dict[str, Any]:
    """最小化的测试企业数据（只包含必填字段）"""
    timestamp = int(time.time() * 1000)
    return {
        "credit_code": f"91110000MA{timestamp:010d}"[-18:],
        "enterprise_name": f"最小测试企业_{timestamp}",
        "status": "存续",
    }


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPICreate:
    """测试企业信息创建 API"""

    async def test_create_enterprise_full_data(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试创建完整企业信息"""
        response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["msg"] == "企业基础信息创建成功"
        assert data["data"] is not None
        
        enterprise = data["data"]
        assert enterprise["credit_code"] == test_enterprise_data["credit_code"]
        assert enterprise["enterprise_name"] == test_enterprise_data["enterprise_name"]
        assert enterprise["status"] == test_enterprise_data["status"]
        assert enterprise["legal_representative"] == test_enterprise_data["legal_representative"]
        assert enterprise["registered_capital"] == test_enterprise_data["registered_capital"]
        assert enterprise["establishment_date"] == test_enterprise_data["establishment_date"]
        assert enterprise["enterprise_type"] == test_enterprise_data["enterprise_type"]
        assert enterprise["registration_authority"] == test_enterprise_data["registration_authority"]
        assert enterprise["registered_address"] == test_enterprise_data["registered_address"]
        assert enterprise["id"] is not None
        assert enterprise["created_at"] is not None
        assert enterprise["updated_at"] is not None

    async def test_create_enterprise_minimal_data(self, client: httpx.AsyncClient, test_enterprise_data_minimal: Dict[str, Any]):
        """测试创建最小化企业信息（只包含必填字段）"""
        response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data_minimal,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 0
        assert data["data"] is not None
        enterprise = data["data"]
        assert enterprise["credit_code"] == test_enterprise_data_minimal["credit_code"]
        assert enterprise["enterprise_name"] == test_enterprise_data_minimal["enterprise_name"]
        assert enterprise["status"] == test_enterprise_data_minimal["status"]

    async def test_create_enterprise_duplicate_credit_code(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试创建重复信用代码的企业（应该失败）"""
        # 先创建一个
        response1 = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        assert response1.status_code == 200
        assert response1.json()["code"] == 0
        
        # 尝试用相同的信用代码创建（应该失败）
        response2 = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        
        assert response2.status_code == 200
        data = response2.json()
        assert data["code"] != 0  # 应该返回错误
        assert "已存在" in data["msg"] or "credit_code" in data["msg"].lower()

    async def test_create_enterprise_missing_required_fields(self, client: httpx.AsyncClient):
        """测试缺少必填字段的创建请求"""
        # 缺少 credit_code
        response = await client.post(
            "/api/v1/enterprise/basic-info",
            json={
                "enterprise_name": "测试企业",
                "status": "存续",
            },
        )
        assert response.status_code == 422  # FastAPI 验证错误


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPIRead:
    """测试企业信息查询 API"""

    async def test_get_enterprise_by_id(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试根据ID查询企业信息"""
        # 先创建一个企业
        create_response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        assert create_response.status_code == 200
        created_enterprise = create_response.json()["data"]
        enterprise_id = created_enterprise["id"]
        
        # 根据ID查询
        response = await client.get(f"/api/v1/enterprise/basic-info/{enterprise_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"] is not None
        
        enterprise = data["data"]
        assert enterprise["id"] == enterprise_id
        assert enterprise["credit_code"] == test_enterprise_data["credit_code"]
        assert enterprise["enterprise_name"] == test_enterprise_data["enterprise_name"]

    async def test_get_enterprise_by_id_not_found(self, client: httpx.AsyncClient):
        """测试查询不存在的企业ID"""
        response = await client.get("/api/v1/enterprise/basic-info/99999999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]

    async def test_get_enterprise_by_credit_code(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试根据统一社会信用代码查询企业信息"""
        # 先创建一个企业
        create_response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        assert create_response.status_code == 200
        credit_code = test_enterprise_data["credit_code"]
        
        # 根据信用代码查询
        response = await client.get(f"/api/v1/enterprise/basic-info/by-credit/{credit_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"] is not None
        
        enterprise = data["data"]
        assert enterprise["credit_code"] == credit_code
        assert enterprise["enterprise_name"] == test_enterprise_data["enterprise_name"]

    async def test_get_enterprise_by_credit_code_not_found(self, client: httpx.AsyncClient):
        """测试查询不存在的信用代码"""
        response = await client.get("/api/v1/enterprise/basic-info/by-credit/91110000MA00000000")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPIUpdate:
    """测试企业信息更新 API"""

    async def test_update_enterprise(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试更新企业信息"""
        # 先创建一个企业
        create_response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        assert create_response.status_code == 200
        created_enterprise = create_response.json()["data"]
        enterprise_id = created_enterprise["id"]
        
        # 更新企业信息
        update_data = {
            "enterprise_name": "更新后的企业名称",
            "status": "注销",
            "legal_representative": "李四",
        }
        response = await client.put(
            f"/api/v1/enterprise/basic-info/{enterprise_id}",
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "企业基础信息更新成功"
        
        updated_enterprise = data["data"]
        assert updated_enterprise["id"] == enterprise_id
        assert updated_enterprise["enterprise_name"] == update_data["enterprise_name"]
        assert updated_enterprise["status"] == update_data["status"]
        assert updated_enterprise["legal_representative"] == update_data["legal_representative"]
        # 其他字段应该保持不变
        assert updated_enterprise["credit_code"] == test_enterprise_data["credit_code"]

    async def test_update_enterprise_not_found(self, client: httpx.AsyncClient):
        """测试更新不存在的企业"""
        response = await client.put(
            "/api/v1/enterprise/basic-info/99999999",
            json={
                "enterprise_name": "不存在的企业",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPIDelete:
    """测试企业信息删除 API"""

    async def test_delete_enterprise(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试删除企业信息"""
        # 先创建一个企业
        create_response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        assert create_response.status_code == 200
        created_enterprise = create_response.json()["data"]
        enterprise_id = created_enterprise["id"]
        
        # 删除企业
        response = await client.delete(f"/api/v1/enterprise/basic-info/{enterprise_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "企业基础信息删除成功"
        assert data["data"] is True
        
        # 验证企业已被删除（再次查询应该返回404）
        get_response = await client.get(f"/api/v1/enterprise/basic-info/{enterprise_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["code"] == 404

    async def test_delete_enterprise_not_found(self, client: httpx.AsyncClient):
        """测试删除不存在的企业"""
        response = await client.delete("/api/v1/enterprise/basic-info/99999999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPICRUD:
    """测试完整的 CRUD 流程"""

    async def test_full_crud_workflow(self, client: httpx.AsyncClient, test_enterprise_data: Dict[str, Any]):
        """测试完整的创建-读取-更新-删除流程"""
        # 1. 创建
        create_response = await client.post(
            "/api/v1/enterprise/basic-info",
            json=test_enterprise_data,
        )
        assert create_response.status_code == 200
        created = create_response.json()["data"]
        enterprise_id = created["id"]
        credit_code = created["credit_code"]
        
        # 2. 读取（通过ID）
        get_response = await client.get(f"/api/v1/enterprise/basic-info/{enterprise_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["id"] == enterprise_id
        
        # 3. 读取（通过信用代码）
        get_by_credit_response = await client.get(f"/api/v1/enterprise/basic-info/by-credit/{credit_code}")
        assert get_by_credit_response.status_code == 200
        assert get_by_credit_response.json()["data"]["credit_code"] == credit_code
        
        # 4. 更新
        update_response = await client.put(
            f"/api/v1/enterprise/basic-info/{enterprise_id}",
            json={"enterprise_name": "更新后的名称"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["enterprise_name"] == "更新后的名称"
        
        # 5. 删除
        delete_response = await client.delete(f"/api/v1/enterprise/basic-info/{enterprise_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["data"] is True
        
        # 6. 验证已删除
        final_get_response = await client.get(f"/api/v1/enterprise/basic-info/{enterprise_id}")
        assert final_get_response.json()["code"] == 404


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPICSVUpload:
    """测试 CSV 上传 API"""

    async def test_upload_csv_valid(self, client: httpx.AsyncClient):
        """测试上传有效的 CSV 文件"""
        timestamp = int(time.time() * 1000)
        # 生成唯一的信用代码（确保18位）
        credit_code1 = f"91110000MA{timestamp:010d}"[-18:]
        credit_code2 = f"91110000MA{timestamp+1:010d}"[-18:]
        
        csv_content = f"""credit_code,enterprise_name,status,legal_representative,registered_capital,establishment_date,enterprise_type,registration_authority,registered_address
{credit_code1},CSV测试企业1_{timestamp},存续,张三,1000万元,2020-01-01,有限责任公司,北京市市场监督管理局,北京市朝阳区
{credit_code2},CSV测试企业2_{timestamp},存续,李四,2000万元,2020-02-01,股份有限公司,上海市市场监督管理局,上海市浦东新区
"""
        
        # 创建文件对象
        files = {
            "file": ("test_enterprises.csv", csv_content.encode("utf-8"), "text/csv")
        }
        
        response = await client.post(
            "/api/v1/enterprise/basic-info/upload-csv",
            files=files,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "CSV 导入成功" in data["msg"]
        assert data["data"] is not None
        assert len(data["data"]) == 2

    async def test_upload_csv_invalid_format(self, client: httpx.AsyncClient):
        """测试上传非 CSV 文件"""
        files = {
            "file": ("test.txt", "这不是CSV文件".encode("utf-8"), "text/plain")
        }
        
        response = await client.post(
            "/api/v1/enterprise/basic-info/upload-csv",
            files=files,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0
        assert "CSV" in data["msg"]

    async def test_upload_csv_missing_required_fields(self, client: httpx.AsyncClient):
        """测试上传缺少必填字段的 CSV"""
        csv_content = """credit_code,enterprise_name
91110000MA00000001,测试企业
"""
        files = {
            "file": ("test.csv", csv_content.encode("utf-8"), "text/csv")
        }
        
        response = await client.post(
            "/api/v1/enterprise/basic-info/upload-csv",
            files=files,
        )
        
        # 应该返回错误，因为缺少 status 字段
        assert response.status_code in [200, 400, 422]
        data = response.json()
        
        # FastAPI 可能返回标准错误格式 {"detail": "..."} 或我们的 HttpResponse 格式
        if "detail" in data:
            # FastAPI 标准错误格式
            assert "缺少" in data["detail"] or "必填" in data["detail"]
        else:
            # 我们的 HttpResponse 格式
            assert data["code"] != 0 or "缺少" in data.get("msg", "").lower() or "必填" in data.get("msg", "")


@pytest.mark.asyncio
@pytest.mark.integration
class TestEnterpriseAPIServerHealth:
    """测试服务器健康状态"""

    async def test_server_is_running(self, client: httpx.AsyncClient):
        """测试服务器是否正在运行"""
        try:
            response = await client.get("/api/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.fail("无法连接到服务器，请确保服务器正在运行在 http://localhost:8512")

