"""
民法典法条实体

领域实体，表示民法典法条信息
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.tools import current_timestamp_ms


class CivilCodeArticle(BaseModel):
    """
    民法典法条实体
    """

    id: Optional[int] = Field(None, description="主键ID")
    book_no: int = Field(..., description="编编号（如：1 总则编，2 物权编）")
    book_name: str = Field(..., max_length=50, description="编名")
    chapter_no: Optional[int] = Field(None, description="章编号")
    chapter_name: Optional[str] = Field(None, max_length=100, description="章名")
    section_no: Optional[int] = Field(None, description="节编号（可选）")
    section_name: Optional[str] = Field(None, max_length=100, description="节名（可选）")
    article_no: int = Field(..., description="条号（如：第十条 → 10）")
    article_title: Optional[str] = Field(None, max_length=200, description="条标题（如有）")
    article_text: str = Field(..., description="法条全文")
    keywords: Optional[str] = Field(None, description="人工提炼关键词（可选）")
    source_version: str = Field(default="民法典(2021)", max_length=50, description="来源版本")
    created_at: int = Field(..., description="创建时间")

    def update_info(
        self,
        book_no: Optional[int] = None,
        book_name: Optional[str] = None,
        chapter_no: Optional[int] = None,
        chapter_name: Optional[str] = None,
        section_no: Optional[int] = None,
        section_name: Optional[str] = None,
        article_no: Optional[int] = None,
        article_title: Optional[str] = None,
        article_text: Optional[str] = None,
        keywords: Optional[str] = None,
        source_version: Optional[str] = None,
    ) -> None:
        """
        更新法条信息（忽略为 None 的字段）
        """
        if book_no is not None:
            self.book_no = book_no
        if book_name is not None:
            self.book_name = book_name
        if chapter_no is not None:
            self.chapter_no = chapter_no
        if chapter_name is not None:
            self.chapter_name = chapter_name
        if section_no is not None:
            self.section_no = section_no
        if section_name is not None:
            self.section_name = section_name
        if article_no is not None:
            self.article_no = article_no
        if article_title is not None:
            self.article_title = article_title
        if article_text is not None:
            self.article_text = article_text
        if keywords is not None:
            self.keywords = keywords
        if source_version is not None:
            self.source_version = source_version

