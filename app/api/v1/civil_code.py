"""
民法典法条 API 路由（v1版本）

表现层，处理HTTP请求和响应
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query
from sqlalchemy.exc import IntegrityError

from app.models import HttpResponse
from app.exceptions import (
    BadRequestException,
    ServerUnavailableException,
    InternalServerException,
)
from app.domains.civil_code.application.services import (
    CivilCodeArticleApplicationService,
)
from app.domains.civil_code.application.dto import (
    CivilCodeArticleCreateDTO,
    CivilCodeArticleUpdateDTO,
    CivilCodeArticleDTO,
    CivilCodeArticleSearchResultDTO,
)
from app.domains.civil_code.infrastructure.repositories import (
    PostgresCivilCodeArticleRepository,
)


civil_code_router = APIRouter(
    prefix="/api/v1/civil-code", tags=["civil-code-article"]
)


def get_civil_code_service(db_name: str = "law_cn") -> CivilCodeArticleApplicationService:
    """
    获取民法典法条应用服务实例（依赖注入）

    Args:
        db_name: 数据库名称，默认为 'law_cn'
    """
    from app.services.postgres_service import get_postgres_service

    pg_service = get_postgres_service(db_name)
    if pg_service is None or pg_service.engine is None:
        raise RuntimeError(f"PostgreSQL service is not available for database: {db_name}")

    repository = PostgresCivilCodeArticleRepository(db_name=db_name)
    return CivilCodeArticleApplicationService(repository)


@civil_code_router.post(
    "/articles",
    response_model=HttpResponse[CivilCodeArticleDTO],
)
async def create_civil_code_article(
    data: CivilCodeArticleCreateDTO,
) -> HttpResponse[CivilCodeArticleDTO]:
    """
    创建民法典法条
    """
    try:
        service = get_civil_code_service()
        created = await service.create_article(data)
        return HttpResponse.success(data=created, msg="法条创建成功")
    except IntegrityError:
        # 违反唯一约束（如 book_no + article_no 已存在）
        return HttpResponse.duplicate(
            f"法条创建失败：该编号和条号已存在（book_no={data.book_no}, article_no={data.article_no}）"
        )
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"创建法条失败: {str(e)}")


@civil_code_router.get(
    "/articles/search",
    response_model=HttpResponse[CivilCodeArticleSearchResultDTO],
)
async def search_civil_code_articles(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> HttpResponse[CivilCodeArticleSearchResultDTO]:
    """
    全文搜索民法典法条
    """
    try:
        service = get_civil_code_service()
        result = await service.search_articles(query=q, limit=limit, offset=offset)
        return HttpResponse.success(data=result, msg="搜索成功")
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"搜索法条失败: {str(e)}")


@civil_code_router.get(
    "/articles/by-book-article",
    response_model=HttpResponse[CivilCodeArticleDTO],
)
async def get_civil_code_article_by_book_and_article(
    book_no: int = Query(..., description="编编号"),
    article_no: int = Query(..., description="条号"),
) -> HttpResponse[CivilCodeArticleDTO]:
    """
    根据编号和条号查询民法典法条
    """
    try:
        service = get_civil_code_service()
        article = await service.get_article_by_book_and_article(book_no, article_no)
        if article is None:
            return HttpResponse.notfound(
                f"法条不存在: book_no={book_no}, article_no={article_no}"
            )
        return HttpResponse.success(data=article, msg="查询成功")
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"查询法条失败: {str(e)}")


@civil_code_router.get(
    "/articles/{article_id}",
    response_model=HttpResponse[CivilCodeArticleDTO],
)
async def get_civil_code_article(
    article_id: int,
) -> HttpResponse[CivilCodeArticleDTO]:
    """
    根据ID查询民法典法条
    """
    try:
        service = get_civil_code_service()
        article = await service.get_article(article_id)
        if article is None:
            return HttpResponse.notfound(f"法条不存在: {article_id}")
        return HttpResponse.success(data=article, msg="查询成功")
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"查询法条失败: {str(e)}")


@civil_code_router.put(
    "/articles/{article_id}",
    response_model=HttpResponse[CivilCodeArticleDTO],
)
async def update_civil_code_article(
    article_id: int,
    data: CivilCodeArticleUpdateDTO,
) -> HttpResponse[CivilCodeArticleDTO]:
    """
    更新民法典法条
    """
    try:
        service = get_civil_code_service()
        updated = await service.update_article(article_id, data)
        if updated is None:
            return HttpResponse.notfound(f"法条不存在: {article_id}")
        return HttpResponse.success(data=updated, msg="法条更新成功")
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"更新法条失败: {str(e)}")


@civil_code_router.delete(
    "/articles/{article_id}",
    response_model=HttpResponse[bool],
)
async def delete_civil_code_article(
    article_id: int,
) -> HttpResponse[bool]:
    """
    删除民法典法条
    """
    try:
        service = get_civil_code_service()
        deleted = await service.delete_article(article_id)
        if not deleted:
            return HttpResponse.notfound(f"法条不存在: {article_id}")
        return HttpResponse.success(data=True, msg="法条删除成功")
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"删除法条失败: {str(e)}")

