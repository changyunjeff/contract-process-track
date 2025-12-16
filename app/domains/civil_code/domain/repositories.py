"""
民法典法条仓储接口

定义领域层需要的仓储接口，由基础设施层实现
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import CivilCodeArticle


class ICivilCodeArticleRepository(ABC):
    """民法典法条仓储接口"""

    @abstractmethod
    async def create(self, article: CivilCodeArticle) -> CivilCodeArticle:
        """
        创建法条
        """

    @abstractmethod
    async def update(self, article: CivilCodeArticle) -> CivilCodeArticle:
        """
        更新法条
        """

    @abstractmethod
    async def get_by_id(self, article_id: int) -> Optional[CivilCodeArticle]:
        """
        根据ID查询法条
        """

    @abstractmethod
    async def get_by_book_and_article(
        self, book_no: int, article_no: int
    ) -> Optional[CivilCodeArticle]:
        """
        根据编号和条号查询法条
        """

    @abstractmethod
    async def search(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> tuple[List[CivilCodeArticle], int]:
        """
        全文搜索法条
        
        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
            offset: 偏移量
        
        Returns:
            (法条列表, 总记录数)
        """

    @abstractmethod
    async def delete(self, article_id: int) -> bool:
        """
        删除法条
        """

