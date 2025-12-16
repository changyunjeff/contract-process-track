"""
民法典法条的数据传输对象（DTO）

用于API接口和领域实体之间的数据传递
"""
from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field


class CivilCodeArticleCreateDTO(BaseModel):
    """创建法条的DTO"""

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
    source_version: Optional[str] = Field(
        default="民法典(2021)", max_length=50, description="来源版本"
    )


class CivilCodeArticleUpdateDTO(BaseModel):
    """更新法条的DTO（全部字段可选，按需更新）"""

    book_no: Optional[int] = Field(None, description="编编号（如：1 总则编，2 物权编）")
    book_name: Optional[str] = Field(None, max_length=50, description="编名")
    chapter_no: Optional[int] = Field(None, description="章编号")
    chapter_name: Optional[str] = Field(None, max_length=100, description="章名")
    section_no: Optional[int] = Field(None, description="节编号（可选）")
    section_name: Optional[str] = Field(None, max_length=100, description="节名（可选）")
    article_no: Optional[int] = Field(None, description="条号（如：第十条 → 10）")
    article_title: Optional[str] = Field(None, max_length=200, description="条标题（如有）")
    article_text: Optional[str] = Field(None, description="法条全文")
    keywords: Optional[str] = Field(None, description="人工提炼关键词（可选）")
    source_version: Optional[str] = Field(None, max_length=50, description="来源版本")


class CivilCodeArticleDTO(BaseModel):
    """对外返回的法条DTO"""

    id: int = Field(..., description="主键ID")
    book_no: int = Field(..., description="编编号（如：1 总则编，2 物权编）")
    book_name: str = Field(..., description="编名")
    chapter_no: Optional[int] = Field(None, description="章编号")
    chapter_name: Optional[str] = Field(None, description="章名")
    section_no: Optional[int] = Field(None, description="节编号（可选）")
    section_name: Optional[str] = Field(None, description="节名（可选）")
    article_no: int = Field(..., description="条号（如：第十条 → 10）")
    article_title: Optional[str] = Field(None, description="条标题（如有）")
    article_text: str = Field(..., description="法条全文")
    keywords: Optional[str] = Field(None, description="人工提炼关键词（可选）")
    source_version: str = Field(..., description="来源版本")
    created_at: int = Field(..., description="创建时间")


class CivilCodeArticleSearchResultDTO(BaseModel):
    """法条搜索结果DTO"""

    articles: List[CivilCodeArticleDTO] = Field(..., description="法条列表")
    total: int = Field(..., description="总记录数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")

