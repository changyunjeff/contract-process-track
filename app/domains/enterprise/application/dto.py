"""
工商企业基础信息的数据传输对象（DTO）

用于API接口和领域实体之间的数据传递
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class EnterpriseBasicInfoCreateDTO(BaseModel):
    """创建企业基础信息的DTO"""

    credit_code: str = Field(..., max_length=18, description="统一社会信用代码")
    enterprise_name: str = Field(..., max_length=255, description="企业名称")
    status: str = Field(..., max_length=10, description="企业状态")

    legal_representative: Optional[str] = Field(
        None, max_length=100, description="法定代表人"
    )
    registered_capital: Optional[str] = Field(
        None, max_length=50, description="注册资本（原始字符串）"
    )
    establishment_date: Optional[date] = Field(
        None, description="成立日期（YYYY-MM-DD）"
    )

    enterprise_type: Optional[str] = Field(
        None, max_length=100, description="企业类型"
    )
    registration_authority: Optional[str] = Field(
        None, max_length=200, description="登记机关"
    )
    registered_address: Optional[str] = Field(
        None, description="注册地址"
    )


class EnterpriseBasicInfoUpdateDTO(BaseModel):
    """更新企业基础信息的DTO（全部字段可选，按需更新）"""

    credit_code: Optional[str] = Field(
        None, max_length=18, description="统一社会信用代码"
    )
    enterprise_name: Optional[str] = Field(
        None, max_length=255, description="企业名称"
    )
    status: Optional[str] = Field(None, max_length=10, description="企业状态")

    legal_representative: Optional[str] = Field(
        None, max_length=100, description="法定代表人"
    )
    registered_capital: Optional[str] = Field(
        None, max_length=50, description="注册资本（原始字符串）"
    )
    establishment_date: Optional[date] = Field(
        None, description="成立日期（YYYY-MM-DD）"
    )

    enterprise_type: Optional[str] = Field(
        None, max_length=100, description="企业类型"
    )
    registration_authority: Optional[str] = Field(
        None, max_length=200, description="登记机关"
    )
    registered_address: Optional[str] = Field(
        None, description="注册地址"
    )


class EnterpriseBasicInfoDTO(BaseModel):
    """对外返回的企业基础信息DTO"""

    id: int = Field(..., description="主键ID")
    credit_code: str = Field(..., description="统一社会信用代码")
    enterprise_name: str = Field(..., description="企业名称")
    status: str = Field(..., description="企业状态")

    legal_representative: Optional[str] = Field(
        None, description="法定代表人"
    )
    registered_capital: Optional[str] = Field(
        None, description="注册资本（原始字符串）"
    )
    establishment_date: Optional[date] = Field(
        None, description="成立日期（YYYY-MM-DD）"
    )

    enterprise_type: Optional[str] = Field(
        None, description="企业类型"
    )
    registration_authority: Optional[str] = Field(
        None, description="登记机关"
    )
    registered_address: Optional[str] = Field(
        None, description="注册地址"
    )

    created_at: int = Field(..., description="创建时间")
    updated_at: int = Field(..., description="更新时间")



