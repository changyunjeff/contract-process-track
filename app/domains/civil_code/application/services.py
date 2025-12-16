"""
民法典法条应用服务

应用层服务，协调领域对象和仓储，实现业务用例
"""
from __future__ import annotations

import logging
from typing import Optional, List

from ..domain.entities import CivilCodeArticle
from ..domain.repositories import ICivilCodeArticleRepository
from .dto import (
    CivilCodeArticleCreateDTO,
    CivilCodeArticleUpdateDTO,
    CivilCodeArticleDTO,
    CivilCodeArticleSearchResultDTO,
)
from app.tools import current_timestamp_ms

logger = logging.getLogger(__name__)


class CivilCodeArticleApplicationService:
    """民法典法条应用服务"""

    def __init__(self, repository: ICivilCodeArticleRepository) -> None:
        """
        初始化应用服务

        Args:
            repository: 法条仓储
        """
        self.repository = repository

    async def create_article(
        self, dto: CivilCodeArticleCreateDTO
    ) -> CivilCodeArticleDTO:
        """
        创建法条
        """
        now = current_timestamp_ms()
        entity = CivilCodeArticle(
            id=None,
            book_no=dto.book_no,
            book_name=dto.book_name,
            chapter_no=dto.chapter_no,
            chapter_name=dto.chapter_name,
            section_no=dto.section_no,
            section_name=dto.section_name,
            article_no=dto.article_no,
            article_title=dto.article_title,
            article_text=dto.article_text,
            keywords=dto.keywords,
            source_version=dto.source_version or "民法典(2021)",
            created_at=now,
        )

        try:
            created = await self.repository.create(entity)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Failed to create civil code article: book_no=%s, article_no=%s",
                dto.book_no,
                dto.article_no,
            )
            raise

        logger.info(
            "Created civil code article: book_no=%s, article_no=%s",
            created.book_no,
            created.article_no,
        )
        return self._entity_to_dto(created)

    async def update_article(
        self, article_id: int, dto: CivilCodeArticleUpdateDTO
    ) -> Optional[CivilCodeArticleDTO]:
        """
        更新法条
        """
        existing = await self.repository.get_by_id(article_id)
        if not existing:
            return None

        existing.update_info(
            book_no=dto.book_no,
            book_name=dto.book_name,
            chapter_no=dto.chapter_no,
            chapter_name=dto.chapter_name,
            section_no=dto.section_no,
            section_name=dto.section_name,
            article_no=dto.article_no,
            article_title=dto.article_title,
            article_text=dto.article_text,
            keywords=dto.keywords,
            source_version=dto.source_version,
        )

        updated = await self.repository.update(existing)
        logger.info("Updated civil code article: id=%s", article_id)
        return self._entity_to_dto(updated)

    async def get_article(
        self, article_id: int
    ) -> Optional[CivilCodeArticleDTO]:
        """
        根据ID查询法条
        """
        entity = await self.repository.get_by_id(article_id)
        if not entity:
            return None
        return self._entity_to_dto(entity)

    async def get_article_by_book_and_article(
        self, book_no: int, article_no: int
    ) -> Optional[CivilCodeArticleDTO]:
        """
        根据编号和条号查询法条
        """
        entity = await self.repository.get_by_book_and_article(book_no, article_no)
        if not entity:
            return None
        return self._entity_to_dto(entity)

    async def search_articles(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> CivilCodeArticleSearchResultDTO:
        """
        全文搜索法条
        """
        articles, total = await self.repository.search(query, limit=limit, offset=offset)
        return CivilCodeArticleSearchResultDTO(
            articles=[self._entity_to_dto(article) for article in articles],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def delete_article(self, article_id: int) -> bool:
        """
        删除法条
        """
        result = await self.repository.delete(article_id)
        if result:
            logger.info("Deleted civil code article: id=%s", article_id)
        return result

    def _entity_to_dto(self, entity: CivilCodeArticle) -> CivilCodeArticleDTO:
        """将领域实体转换为DTO"""
        if entity.id is None:
            raise ValueError(
                "CivilCodeArticle.id should not be None when mapping to DTO"
            )

        return CivilCodeArticleDTO(
            id=entity.id,
            book_no=entity.book_no,
            book_name=entity.book_name,
            chapter_no=entity.chapter_no,
            chapter_name=entity.chapter_name,
            section_no=entity.section_no,
            section_name=entity.section_name,
            article_no=entity.article_no,
            article_title=entity.article_title,
            article_text=entity.article_text,
            keywords=entity.keywords,
            source_version=entity.source_version,
            created_at=entity.created_at,
        )

