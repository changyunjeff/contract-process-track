"""
工商企业基础信息实体

领域实体，表示工商注册企业的基本信息
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field
from app.tools import current_timestamp_ms


class EnterpriseBasicInfo(BaseModel):
    """
    工商企业基础信息实体
    """

    id: Optional[int] = Field(None, description="主键ID")
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

    created_at: int = Field(..., description="创建时间")
    updated_at: int = Field(..., description="更新时间")

    def update_info(
        self,
        credit_code: Optional[str] = None,
        enterprise_name: Optional[str] = None,
        status: Optional[str] = None,
        legal_representative: Optional[str] = None,
        registered_capital: Optional[str] = None,
        establishment_date: Optional[date] = None,
        enterprise_type: Optional[str] = None,
        registration_authority: Optional[str] = None,
        registered_address: Optional[str] = None,
    ) -> None:
        """
        更新企业基础信息（忽略为 None 的字段）
        """
        if credit_code is not None:
            self.credit_code = credit_code
        if enterprise_name is not None:
            self.enterprise_name = enterprise_name
        if status is not None:
            self.status = status
        if legal_representative is not None:
            self.legal_representative = legal_representative
        if registered_capital is not None:
            self.registered_capital = registered_capital
        if establishment_date is not None:
            self.establishment_date = establishment_date
        if enterprise_type is not None:
            self.enterprise_type = enterprise_type
        if registration_authority is not None:
            self.registration_authority = registration_authority
        if registered_address is not None:
            self.registered_address = registered_address

        self.updated_at = current_timestamp_ms()



