"""
工商企业基础信息仓储接口

定义领域层需要的仓储接口，由基础设施层实现
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import EnterpriseBasicInfo


class IEnterpriseBasicInfoRepository(ABC):
    """工商企业基础信息仓储接口"""

    @abstractmethod
    async def create(self, enterprise: EnterpriseBasicInfo) -> EnterpriseBasicInfo:
        """
        创建企业基础信息
        """

    @abstractmethod
    async def update(self, enterprise: EnterpriseBasicInfo) -> EnterpriseBasicInfo:
        """
        更新企业基础信息
        """

    @abstractmethod
    async def get_by_id(self, enterprise_id: int) -> Optional[EnterpriseBasicInfo]:
        """
        根据ID查询企业基础信息
        """

    @abstractmethod
    async def get_by_credit_code(
        self, credit_code: str
    ) -> Optional[EnterpriseBasicInfo]:
        """
        根据统一社会信用代码查询企业基础信息
        """

    @abstractmethod
    async def delete(self, enterprise_id: int) -> bool:
        """
        删除企业基础信息
        """



