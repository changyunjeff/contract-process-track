"""
真实 API 集成测试：测试工具相关 API

这些测试直接调用 http://localhost:8512 上的实际 API 端点
确保服务器已启动：python main.py 或 uvicorn main:app --host 0.0.0.0 --port 8512
"""
from __future__ import annotations

import pytest
import httpx
from typing import Dict, Any


# 测试服务器地址
BASE_URL = "http://localhost:8512"


@pytest.fixture
def client():
    """创建 HTTP 客户端"""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.mark.asyncio
@pytest.mark.integration
class TestToolAPIList:
    """测试工具列表 API"""

    async def test_list_tools(self, client: httpx.AsyncClient):
        """测试获取所有工具列表"""
        response = await client.get("/api/v1/tools/")
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["msg"] == "获取工具列表成功"
        assert data["data"] is not None
        
        tools_data = data["data"]
        assert "tools" in tools_data
        assert "count" in tools_data
        assert isinstance(tools_data["tools"], list)
        assert tools_data["count"] >= 0
        
        # 验证工具列表不为空（至少应该有 ocr_parser）
        assert tools_data["count"] > 0, "应该至少有一个工具"
        
        # 验证工具结构
        if tools_data["tools"]:
            tool = tools_data["tools"][0]
            assert "name" in tool
            assert "description" in tool
            assert "parameters_schema" in tool
            assert isinstance(tool["parameters_schema"], dict)

    async def test_list_tools_openai_format(self, client: httpx.AsyncClient):
        """测试获取工具列表（OpenAI格式，兼容Langdock）"""
        response = await client.get("/api/v1/tools/openai")
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["msg"] == "获取工具列表成功（OpenAI格式）"
        assert data["data"] is not None
        
        tools_data = data["data"]
        assert "tools" in tools_data
        assert "count" in tools_data
        assert isinstance(tools_data["tools"], list)
        assert tools_data["count"] >= 0
        
        # 验证OpenAI格式
        if tools_data["tools"]:
            tool = tools_data["tools"][0]
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestToolAPIDetail:
    """测试工具详情 API"""

    async def test_get_tool_info_existing(self, client: httpx.AsyncClient):
        """测试获取存在的工具详情"""
        # 假设 ocr_parser 工具存在
        tool_name = "ocr_parser"
        response = await client.get(f"/api/v1/tools/{tool_name}")
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["msg"] == "获取工具信息成功"
        assert data["data"] is not None
        
        tool_info = data["data"]
        assert tool_info["name"] == tool_name
        assert "description" in tool_info
        assert "parameters_schema" in tool_info
        assert isinstance(tool_info["parameters_schema"], dict)

    async def test_get_tool_info_not_found(self, client: httpx.AsyncClient):
        """测试获取不存在的工具详情"""
        tool_name = "non_existent_tool"
        response = await client.get(f"/api/v1/tools/{tool_name}")
        
        # NotFoundException 会直接返回 HTTP 404，而不是 HttpResponse 格式
        assert response.status_code == 404
        data = response.json()
        # FastAPI HTTPException 返回 {"detail": "..."} 格式
        assert "detail" in data
        assert "不存在" in data["detail"] or "not found" in data["detail"].lower()

    async def test_get_tool_openai_schema_existing(self, client: httpx.AsyncClient):
        """测试获取存在的工具的OpenAI格式定义"""
        tool_name = "ocr_parser"
        response = await client.get(f"/api/v1/tools/{tool_name}/openai")
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["msg"] == "获取工具OpenAI格式定义成功"
        assert data["data"] is not None
        
        schema = data["data"]
        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema
        assert schema["function"]["name"] == tool_name
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]

    async def test_get_tool_openai_schema_not_found(self, client: httpx.AsyncClient):
        """测试获取不存在工具的OpenAI格式定义"""
        tool_name = "non_existent_tool"
        response = await client.get(f"/api/v1/tools/{tool_name}/openai")
        
        # NotFoundException 会直接返回 HTTP 404，而不是 HttpResponse 格式
        assert response.status_code == 404
        data = response.json()
        # FastAPI HTTPException 返回 {"detail": "..."} 格式
        assert "detail" in data
        assert "不存在" in data["detail"] or "not found" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
class TestToolAPIExecute:
    """测试工具执行 API"""

    async def test_execute_tool_general_interface(self, client: httpx.AsyncClient):
        """测试通用工具执行接口"""
        request_data = {
            "tool_name": "ocr_parser",
            "input": {
                "image_path": "/tmp/non_existent_image.jpg",
                "lang": "chi_sim"
            },
            "context": {}
        }
        
        response = await client.post(
            "/api/v1/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["data"] is not None
        
        result = data["data"]
        assert "tool_name" in result
        assert result["tool_name"] == "ocr_parser"
        assert "result" in result
        assert "success" in result
        # 由于文件不存在，success 应该是 False
        assert isinstance(result["success"], bool)
        assert "type" in result["result"]

    async def test_execute_tool_by_name_interface(self, client: httpx.AsyncClient):
        """测试通过工具名称执行工具（便捷接口）"""
        tool_name = "ocr_parser"
        request_data = {
            "input": {
                "image_path": "/tmp/non_existent_image.jpg",
                "lang": "eng"
            },
            "context": {}
        }
        
        response = await client.post(
            f"/api/v1/tools/{tool_name}/execute",
            json=request_data
        )
        
        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()
        
        assert data["code"] == 0, f"Error response: {data}"
        assert data["data"] is not None
        
        result = data["data"]
        assert result["tool_name"] == tool_name
        assert "result" in result
        assert "success" in result

    async def test_execute_tool_not_found(self, client: httpx.AsyncClient):
        """测试执行不存在的工具"""
        request_data = {
            "tool_name": "non_existent_tool",
            "input": {
                "test_param": "test_value"
            }
        }
        
        response = await client.post(
            "/api/v1/tools/execute",
            json=request_data
        )
        
        # NotFoundException 会直接返回 HTTP 404，而不是 HttpResponse 格式
        assert response.status_code == 404
        data = response.json()
        # FastAPI HTTPException 返回 {"detail": "..."} 格式
        assert "detail" in data
        assert "不存在" in data["detail"] or "not found" in data["detail"].lower()

    async def test_execute_tool_missing_required_parameter(self, client: httpx.AsyncClient):
        """测试缺少必需参数的工具执行"""
        request_data = {
            "tool_name": "ocr_parser",
            "input": {
                # 缺少 image_path
                "lang": "chi_sim"
            }
        }
        
        response = await client.post(
            "/api/v1/tools/execute",
            json=request_data
        )
        
        # BadRequestException 会直接返回 HTTP 400，因为 image_path 是必需的
        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException 返回 {"detail": "..."} 格式
        assert "detail" in data
        assert "参数错误" in data["detail"] or "required" in data["detail"].lower() or "image_path" in data["detail"].lower()

    async def test_execute_tool_with_invalid_input(self, client: httpx.AsyncClient):
        """测试使用无效输入执行工具"""
        request_data = {
            "tool_name": "ocr_parser",
            "input": {
                "image_path": None,  # 无效的输入
            }
        }
        
        response = await client.post(
            "/api/v1/tools/execute",
            json=request_data
        )
        
        # None 值可能导致 FastAPI 验证错误 (422) 或 BadRequestException (400)
        assert response.status_code in [400, 422]
        data = response.json()
        # FastAPI 验证错误返回 {"detail": [...]} 格式
        # BadRequestException 返回 {"detail": "..."} 格式
        assert "detail" in data


@pytest.mark.asyncio
@pytest.mark.integration
class TestToolAPILangdockCompatibility:
    """测试 Langdock 兼容性"""

    async def test_openai_format_compatibility(self, client: httpx.AsyncClient):
        """测试 OpenAI 格式兼容性（Langdock 需要）"""
        # 获取工具列表（OpenAI格式）
        response = await client.get("/api/v1/tools/openai")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 0
        
        tools = data["data"]["tools"]
        assert len(tools) > 0
        
        # 验证每个工具都符合 OpenAI Function Calling 格式
        for tool in tools:
            assert "type" in tool
            assert tool["type"] == "function"
            assert "function" in tool
            
            function = tool["function"]
            assert "name" in function
            assert "description" in function
            assert "parameters" in function
            
            # 验证 parameters 是有效的 JSON Schema
            params = function["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params or "required" in params

    async def test_tool_execution_for_langdock(self, client: httpx.AsyncClient):
        """测试工具执行（Langdock 调用方式）"""
        # Langdock 通常会调用 /api/v1/tools/execute
        request_data = {
            "tool_name": "ocr_parser",
            "input": {
                "image_path": "/tmp/test.jpg",
                "lang": "chi_sim"
            }
        }
        
        response = await client.post(
            "/api/v1/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应格式符合预期
        assert "code" in data
        assert "data" in data or "msg" in data
        
        if data["code"] == 0:
            result = data["data"]
            assert "tool_name" in result
            assert "result" in result
            assert "success" in result


@pytest.mark.asyncio
@pytest.mark.integration
class TestToolAPIServerHealth:
    """测试服务器健康状态"""

    async def test_server_is_running(self, client: httpx.AsyncClient):
        """测试服务器是否正在运行"""
        try:
            response = await client.get("/api/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.fail("无法连接到服务器，请确保服务器正在运行在 http://localhost:8512")


@pytest.mark.asyncio
@pytest.mark.integration
class TestToolAPICRUD:
    """测试完整的工具 API 流程"""

    async def test_full_tool_api_workflow(self, client: httpx.AsyncClient):
        """测试完整的工具 API 使用流程"""
        tool_name = "ocr_parser"
        
        # 1. 获取工具列表
        list_response = await client.get("/api/v1/tools/")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["code"] == 0
        assert any(t["name"] == tool_name for t in list_data["data"]["tools"])
        
        # 2. 获取工具详情
        detail_response = await client.get(f"/api/v1/tools/{tool_name}")
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["code"] == 0
        assert detail_data["data"]["name"] == tool_name
        
        # 3. 获取工具 OpenAI 格式定义
        openai_response = await client.get(f"/api/v1/tools/{tool_name}/openai")
        assert openai_response.status_code == 200
        openai_data = openai_response.json()
        assert openai_data["code"] == 0
        assert openai_data["data"]["function"]["name"] == tool_name
        
        # 4. 执行工具（使用通用接口）
        execute_response = await client.post(
            "/api/v1/tools/execute",
            json={
                "tool_name": tool_name,
                "input": {
                    "image_path": "/tmp/test.jpg"
                }
            }
        )
        assert execute_response.status_code == 200
        execute_data = execute_response.json()
        assert execute_data["code"] == 0
        assert execute_data["data"]["tool_name"] == tool_name
        
        # 5. 执行工具（使用便捷接口）
        execute_by_name_response = await client.post(
            f"/api/v1/tools/{tool_name}/execute",
            json={
                "input": {
                    "image_path": "/tmp/test2.jpg"
                }
            }
        )
        assert execute_by_name_response.status_code == 200
        execute_by_name_data = execute_by_name_response.json()
        assert execute_by_name_data["code"] == 0
        assert execute_by_name_data["data"]["tool_name"] == tool_name

