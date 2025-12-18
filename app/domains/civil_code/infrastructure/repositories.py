"""
PostgreSQL 民法典法条仓储实现

基础设施层实现，负责与 PostgreSQL 交互
"""
from __future__ import annotations

import logging
from typing import Optional, Mapping, Any, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..domain.entities import CivilCodeArticle
from ..domain.repositories import ICivilCodeArticleRepository
from app.services.postgres_service import get_async_session_factory
from app.common import datetime_to_timestamp_ms


logger = logging.getLogger(__name__)


class PostgresCivilCodeArticleRepository(ICivilCodeArticleRepository):
    """基于 PostgreSQL 的法条仓储实现"""

    def __init__(self, db_name: str = "law_cn") -> None:
        """
        初始化仓储

        Args:
            db_name: 数据库名称，默认为 'law_cn'
        """
        self._db_name = db_name
        self._session_factory: async_sessionmaker[AsyncSession] = (
            get_async_session_factory(db_name)
        )

    async def _row_to_entity(self, row: Mapping[str, Any]) -> CivilCodeArticle:
        """
        将数据库行转换为领域实体

        - 数据库中的 created_at 为 TIMESTAMP
        - 领域实体中使用毫秒级时间戳（int）
        """
        created_at_dt = row["created_at"]

        return CivilCodeArticle(
            id=row["id"],
            book_no=row["book_no"],
            book_name=row["book_name"],
            chapter_no=row.get("chapter_no"),
            chapter_name=row.get("chapter_name"),
            section_no=row.get("section_no"),
            section_name=row.get("section_name"),
            article_no=row["article_no"],
            article_title=row.get("article_title"),
            article_text=row["article_text"],
            keywords=row.get("keywords"),
            source_version=row.get("source_version", "民法典(2021)"),
            created_at=datetime_to_timestamp_ms(created_at_dt),
        )

    async def create(self, article: CivilCodeArticle) -> CivilCodeArticle:
        """创建法条"""
        async with self._session_factory() as session:
            stmt = text(
                """
                INSERT INTO civil_code_article (
                    book_no,
                    book_name,
                    chapter_no,
                    chapter_name,
                    section_no,
                    section_name,
                    article_no,
                    article_title,
                    article_text,
                    keywords,
                    source_version
                ) VALUES (
                    :book_no,
                    :book_name,
                    :chapter_no,
                    :chapter_name,
                    :section_no,
                    :section_name,
                    :article_no,
                    :article_title,
                    :article_text,
                    :keywords,
                    :source_version
                )
                RETURNING
                    id,
                    book_no,
                    book_name,
                    chapter_no,
                    chapter_name,
                    section_no,
                    section_name,
                    article_no,
                    article_title,
                    article_text,
                    keywords,
                    source_version,
                    created_at
                """
            )
            params = {
                "book_no": article.book_no,
                "book_name": article.book_name,
                "chapter_no": article.chapter_no,
                "chapter_name": article.chapter_name,
                "section_no": article.section_no,
                "section_name": article.section_name,
                "article_no": article.article_no,
                "article_title": article.article_title,
                "article_text": article.article_text,
                "keywords": article.keywords,
                "source_version": article.source_version,
            }
            result = await session.execute(stmt, params)
            await session.commit()
            row = result.mappings().one()
            created = await self._row_to_entity(row)
            logger.info(
                "Inserted civil_code_article: id=%s, book_no=%s, article_no=%s",
                created.id,
                created.book_no,
                created.article_no,
            )
            return created

    async def update(self, article: CivilCodeArticle) -> CivilCodeArticle:
        """更新法条"""
        if article.id is None:
            raise ValueError("article.id is required for update")

        async with self._session_factory() as session:
            stmt = text(
                """
                UPDATE civil_code_article
                SET
                    book_no = :book_no,
                    book_name = :book_name,
                    chapter_no = :chapter_no,
                    chapter_name = :chapter_name,
                    section_no = :section_no,
                    section_name = :section_name,
                    article_no = :article_no,
                    article_title = :article_title,
                    article_text = :article_text,
                    keywords = :keywords,
                    source_version = :source_version
                WHERE id = :id
                RETURNING
                    id,
                    book_no,
                    book_name,
                    chapter_no,
                    chapter_name,
                    section_no,
                    section_name,
                    article_no,
                    article_title,
                    article_text,
                    keywords,
                    source_version,
                    created_at
                """
            )
            params = {
                "id": article.id,
                "book_no": article.book_no,
                "book_name": article.book_name,
                "chapter_no": article.chapter_no,
                "chapter_name": article.chapter_name,
                "section_no": article.section_no,
                "section_name": article.section_name,
                "article_no": article.article_no,
                "article_title": article.article_title,
                "article_text": article.article_text,
                "keywords": article.keywords,
                "source_version": article.source_version,
            }
            result = await session.execute(stmt, params)
            await session.commit()
            row = result.mappings().one()
            updated = await self._row_to_entity(row)
            logger.info(
                "Updated civil_code_article: id=%s, book_no=%s, article_no=%s",
                updated.id,
                updated.book_no,
                updated.article_no,
            )
            return updated

    async def get_by_id(self, article_id: int) -> Optional[CivilCodeArticle]:
        """根据ID查询法条"""
        async with self._session_factory() as session:
            stmt = text(
                """
                SELECT
                    id,
                    book_no,
                    book_name,
                    chapter_no,
                    chapter_name,
                    section_no,
                    section_name,
                    article_no,
                    article_title,
                    article_text,
                    keywords,
                    source_version,
                    created_at
                FROM civil_code_article
                WHERE id = :id
                """
            )
            result = await session.execute(stmt, {"id": article_id})
            row = result.mappings().one_or_none()
            if row is None:
                return None
            return await self._row_to_entity(row)

    async def get_by_book_and_article(
        self, book_no: int, article_no: int
    ) -> Optional[CivilCodeArticle]:
        """根据编号和条号查询法条"""
        async with self._session_factory() as session:
            stmt = text(
                """
                SELECT
                    id,
                    book_no,
                    book_name,
                    chapter_no,
                    chapter_name,
                    section_no,
                    section_name,
                    article_no,
                    article_title,
                    article_text,
                    keywords,
                    source_version,
                    created_at
                FROM civil_code_article
                WHERE book_no = :book_no AND article_no = :article_no
                """
            )
            result = await session.execute(
                stmt, {"book_no": book_no, "article_no": article_no}
            )
            row = result.mappings().one_or_none()
            if row is None:
                return None
            return await self._row_to_entity(row)

    async def search(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> tuple[List[CivilCodeArticle], int]:
        """全文搜索法条，返回法条列表和总记录数"""
        async with self._session_factory() as session:
            # 先查询总数
            count_stmt = text(
                """
                SELECT COUNT(*) as total
                FROM civil_code_article
                WHERE search_vector @@ plainto_tsquery('simple', :query)
                """
            )
            count_result = await session.execute(count_stmt, {"query": query})
            total = count_result.scalar() or 0

            # 再查询数据
            stmt = text(
                """
                SELECT
                    id,
                    book_no,
                    book_name,
                    chapter_no,
                    chapter_name,
                    section_no,
                    section_name,
                    article_no,
                    article_title,
                    article_text,
                    keywords,
                    source_version,
                    created_at
                FROM civil_code_article
                WHERE search_vector @@ plainto_tsquery('simple', :query)
                ORDER BY ts_rank(search_vector, plainto_tsquery('simple', :query)) DESC
                LIMIT :limit OFFSET :offset
                """
            )
            result = await session.execute(
                stmt, {"query": query, "limit": limit, "offset": offset}
            )
            rows = result.mappings().all()
            articles = [await self._row_to_entity(row) for row in rows]
            return articles, total

    async def delete(self, article_id: int) -> bool:
        """删除法条"""
        async with self._session_factory() as session:
            stmt = text(
                """
                DELETE FROM civil_code_article
                WHERE id = :id
                """
            )
            result = await session.execute(stmt, {"id": article_id})
            await session.commit()
            deleted = result.rowcount or 0
            logger.info(
                "Deleted civil_code_article: id=%s, affected_rows=%s",
                article_id,
                deleted,
            )
            return deleted > 0

