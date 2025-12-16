"""
真实 API 集成测试：民法典法条 API

这些测试直接调用 http://localhost:8512 上的实际 API 端点
确保服务器已启动：python main.py 或 uvicorn main:app --host 0.0.0.0 --port 8512
"""
from __future__ import annotations

import pytest
import httpx
from typing import Dict, Any
import time


# 测试服务器地址
BASE_URL = "http://localhost:8512"


@pytest.fixture
def client():
    """创建 HTTP 客户端"""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


@pytest.fixture
def test_article_data() -> Dict[str, Any]:
    """测试用的法条数据"""
    # 使用时间戳确保唯一性
    timestamp = int(time.time() * 1000)
    return {
        "book_no": 1,
        "book_name": "总则编",
        "chapter_no": 1,
        "chapter_name": "基本规定",
        "section_no": None,
        "section_name": None,
        "article_no": timestamp % 10000,  # 确保条号唯一
        "article_title": f"测试法条标题_{timestamp}",
        "article_text": f"这是测试法条的内容，用于验证API功能。时间戳：{timestamp}",
        "keywords": "测试,法条,API",
        "source_version": "民法典(2021)",
    }


@pytest.fixture
def test_article_data_minimal() -> Dict[str, Any]:
    """最小化的测试法条数据（只包含必填字段）"""
    timestamp = int(time.time() * 1000)
    return {
        "book_no": 2,
        "book_name": "物权编",
        "article_no": timestamp % 10000,
        "article_text": f"最小化测试法条内容_{timestamp}",
    }


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPICreate:
    """测试法条创建 API"""

    async def test_create_article_full_data(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试创建完整法条信息"""
        response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )

        assert response.status_code == 200, f"Response: {response.text}"
        data = response.json()

        assert data["code"] == 0, f"Error response: {data}"
        assert data["msg"] == "法条创建成功"
        assert data["data"] is not None

        article = data["data"]
        assert article["book_no"] == test_article_data["book_no"]
        assert article["book_name"] == test_article_data["book_name"]
        assert article["chapter_no"] == test_article_data["chapter_no"]
        assert article["chapter_name"] == test_article_data["chapter_name"]
        assert article["article_no"] == test_article_data["article_no"]
        assert article["article_title"] == test_article_data["article_title"]
        assert article["article_text"] == test_article_data["article_text"]
        assert article["keywords"] == test_article_data["keywords"]
        assert article["source_version"] == test_article_data["source_version"]
        assert article["id"] is not None
        assert article["created_at"] is not None

    async def test_create_article_minimal_data(
        self,
        client: httpx.AsyncClient,
        test_article_data_minimal: Dict[str, Any],
    ):
        """测试创建最小化法条信息（只包含必填字段）"""
        response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data_minimal,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["code"] == 0
        assert data["data"] is not None
        article = data["data"]
        assert article["book_no"] == test_article_data_minimal["book_no"]
        assert article["book_name"] == test_article_data_minimal["book_name"]
        assert article["article_no"] == test_article_data_minimal["article_no"]
        assert article["article_text"] == test_article_data_minimal["article_text"]

    async def test_create_article_duplicate_book_article(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试创建重复编号和条号的法条（应该失败）"""
        # 先创建一个
        response1 = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert response1.status_code == 200
        assert response1.json()["code"] == 0

        # 尝试用相同的编号和条号创建（应该失败）
        response2 = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["code"] != 0  # 应该返回错误
        assert "已存在" in data["msg"] or "book_no" in data["msg"].lower()

    async def test_create_article_missing_required_fields(
        self, client: httpx.AsyncClient
    ):
        """测试缺少必填字段的创建请求"""
        # 缺少 book_no
        response = await client.post(
            "/api/v1/civil-code/articles",
            json={
                "book_name": "总则编",
                "article_no": 1,
                "article_text": "测试内容",
            },
        )
        assert response.status_code == 422  # FastAPI 验证错误

        # 缺少 article_text
        response = await client.post(
            "/api/v1/civil-code/articles",
            json={
                "book_no": 1,
                "book_name": "总则编",
                "article_no": 1,
            },
        )
        assert response.status_code == 422  # FastAPI 验证错误


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPIRead:
    """测试法条查询 API"""

    async def test_get_article_by_id(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试根据ID查询法条"""
        # 先创建一个法条
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200
        created_article = create_response.json()["data"]
        article_id = created_article["id"]

        # 根据ID查询
        response = await client.get(f"/api/v1/civil-code/articles/{article_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"] is not None

        article = data["data"]
        assert article["id"] == article_id
        assert article["book_no"] == test_article_data["book_no"]
        assert article["article_no"] == test_article_data["article_no"]

    async def test_get_article_by_id_not_found(self, client: httpx.AsyncClient):
        """测试查询不存在的法条ID"""
        response = await client.get("/api/v1/civil-code/articles/99999999")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]

    async def test_get_article_by_book_and_article(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试根据编号和条号查询法条"""
        # 先创建一个法条
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200
        book_no = test_article_data["book_no"]
        article_no = test_article_data["article_no"]

        # 根据编号和条号查询
        response = await client.get(
            f"/api/v1/civil-code/articles/by-book-article",
            params={"book_no": book_no, "article_no": article_no},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"] is not None

        article = data["data"]
        assert article["book_no"] == book_no
        assert article["article_no"] == article_no
        assert article["article_text"] == test_article_data["article_text"]

    async def test_get_article_by_book_and_article_not_found(
        self, client: httpx.AsyncClient
    ):
        """测试查询不存在的编号和条号"""
        response = await client.get(
            "/api/v1/civil-code/articles/by-book-article",
            params={"book_no": 999, "article_no": 99999},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPIUpdate:
    """测试法条更新 API"""

    async def test_update_article(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试更新法条信息"""
        # 先创建一个法条
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200
        created_article = create_response.json()["data"]
        article_id = created_article["id"]

        # 更新法条信息
        update_data = {
            "article_title": "更新后的法条标题",
            "article_text": "更新后的法条内容",
            "keywords": "更新,关键词",
        }
        response = await client.put(
            f"/api/v1/civil-code/articles/{article_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "法条更新成功"

        updated_article = data["data"]
        assert updated_article["id"] == article_id
        assert updated_article["article_title"] == update_data["article_title"]
        assert updated_article["article_text"] == update_data["article_text"]
        assert updated_article["keywords"] == update_data["keywords"]
        # 其他字段应该保持不变
        assert updated_article["book_no"] == test_article_data["book_no"]
        assert updated_article["article_no"] == test_article_data["article_no"]

    async def test_update_article_not_found(self, client: httpx.AsyncClient):
        """测试更新不存在的法条"""
        response = await client.put(
            "/api/v1/civil-code/articles/99999999",
            json={
                "article_text": "不存在的法条",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPIDelete:
    """测试法条删除 API"""

    async def test_delete_article(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试删除法条"""
        # 先创建一个法条
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200
        created_article = create_response.json()["data"]
        article_id = created_article["id"]

        # 删除法条
        response = await client.delete(f"/api/v1/civil-code/articles/{article_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "法条删除成功"
        assert data["data"] is True

        # 验证法条已被删除（再次查询应该返回404）
        get_response = await client.get(f"/api/v1/civil-code/articles/{article_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["code"] == 404

    async def test_delete_article_not_found(self, client: httpx.AsyncClient):
        """测试删除不存在的法条"""
        response = await client.delete("/api/v1/civil-code/articles/99999999")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["msg"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPISearch:
    """测试法条搜索 API"""

    async def test_search_articles(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试全文搜索法条"""
        # 先创建一个法条
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200

        # 等待一下，确保索引已更新（如果需要）
        import asyncio
        await asyncio.sleep(0.5)

        # 搜索法条
        search_query = test_article_data["article_text"].split("，")[0]  # 使用部分文本搜索
        response = await client.get(
            "/api/v1/civil-code/articles/search",
            params={"q": search_query, "limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "搜索成功"
        assert data["data"] is not None

        search_result = data["data"]
        assert "articles" in search_result
        assert "total" in search_result
        assert "limit" in search_result
        assert "offset" in search_result
        assert isinstance(search_result["articles"], list)
        assert search_result["limit"] == 10
        assert search_result["offset"] == 0

    async def test_search_articles_with_pagination(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试分页搜索"""
        # 先创建一个法条
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200

        import asyncio
        await asyncio.sleep(0.5)

        # 第一页
        response1 = await client.get(
            "/api/v1/civil-code/articles/search",
            params={"q": "测试", "limit": 5, "offset": 0},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["code"] == 0
        assert len(data1["data"]["articles"]) <= 5

        # 第二页
        response2 = await client.get(
            "/api/v1/civil-code/articles/search",
            params={"q": "测试", "limit": 5, "offset": 5},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["code"] == 0

    async def test_search_articles_no_results(self, client: httpx.AsyncClient):
        """测试搜索无结果"""
        response = await client.get(
            "/api/v1/civil-code/articles/search",
            params={"q": "这是一个绝对不会匹配的搜索关键词123456789", "limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 0
        assert len(data["data"]["articles"]) == 0


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPICRUD:
    """测试完整的 CRUD 流程"""

    async def test_full_crud_workflow(
        self, client: httpx.AsyncClient, test_article_data: Dict[str, Any]
    ):
        """测试完整的创建-读取-更新-删除流程"""
        # 1. 创建
        create_response = await client.post(
            "/api/v1/civil-code/articles",
            json=test_article_data,
        )
        assert create_response.status_code == 200
        created = create_response.json()["data"]
        article_id = created["id"]
        book_no = created["book_no"]
        article_no = created["article_no"]

        # 2. 读取（通过ID）
        get_response = await client.get(f"/api/v1/civil-code/articles/{article_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["id"] == article_id

        # 3. 读取（通过编号和条号）
        get_by_book_article_response = await client.get(
            "/api/v1/civil-code/articles/by-book-article",
            params={"book_no": book_no, "article_no": article_no},
        )
        assert get_by_book_article_response.status_code == 200
        assert (
            get_by_book_article_response.json()["data"]["book_no"] == book_no
        )
        assert (
            get_by_book_article_response.json()["data"]["article_no"] == article_no
        )

        # 4. 更新
        update_response = await client.put(
            f"/api/v1/civil-code/articles/{article_id}",
            json={"article_title": "更新后的标题"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["data"]["article_title"] == "更新后的标题"

        # 5. 搜索
        import asyncio
        await asyncio.sleep(0.5)
        search_response = await client.get(
            "/api/v1/civil-code/articles/search",
            params={"q": "测试", "limit": 10, "offset": 0},
        )
        assert search_response.status_code == 200
        assert search_response.json()["code"] == 0

        # 6. 删除
        delete_response = await client.delete(
            f"/api/v1/civil-code/articles/{article_id}"
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["data"] is True

        # 7. 验证已删除
        final_get_response = await client.get(
            f"/api/v1/civil-code/articles/{article_id}"
        )
        assert final_get_response.json()["code"] == 404


@pytest.mark.asyncio
@pytest.mark.integration
class TestCivilCodeAPIServerHealth:
    """测试服务器健康状态"""

    async def test_server_is_running(self, client: httpx.AsyncClient):
        """测试服务器是否正在运行"""
        try:
            response = await client.get("/api/health")
            assert response.status_code == 200
        except httpx.ConnectError:
            pytest.fail(
                "无法连接到服务器，请确保服务器正在运行在 http://localhost:8512"
            )

