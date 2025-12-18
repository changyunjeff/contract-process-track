"""
工商企业基础信息应用服务

应用层服务，协调领域对象和仓储，实现业务用例
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from ..domain.entities import EnterpriseBasicInfo
from ..domain.repositories import IEnterpriseBasicInfoRepository
from .dto import (
    EnterpriseBasicInfoCreateDTO,
    EnterpriseBasicInfoUpdateDTO,
    EnterpriseBasicInfoDTO,
)
from app.common import current_timestamp_ms

logger = logging.getLogger(__name__)


class EnterpriseBasicInfoApplicationService:
    """工商企业基础信息应用服务"""

    def __init__(self, repository: IEnterpriseBasicInfoRepository) -> None:
        """
        初始化应用服务

        Args:
            repository: 企业基础信息仓储
        """
        self.repository = repository

    async def create_enterprise(
        self, dto: EnterpriseBasicInfoCreateDTO
    ) -> EnterpriseBasicInfoDTO:
        """
        创建企业基础信息
        """
        now = current_timestamp_ms()
        entity = EnterpriseBasicInfo(
            id=None,
            credit_code=dto.credit_code,
            enterprise_name=dto.enterprise_name,
            status=dto.status,
            legal_representative=dto.legal_representative,
            registered_capital=dto.registered_capital,
            establishment_date=dto.establishment_date,
            enterprise_type=dto.enterprise_type,
            registration_authority=dto.registration_authority,
            registered_address=dto.registered_address,
            created_at=now,
            updated_at=now,
        )

        try:
            created = await self.repository.create(entity)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Failed to create enterprise basic info: credit_code=%s",
                dto.credit_code,
            )
            raise

        logger.info("Created enterprise basic info: %s", created.credit_code)
        return self._entity_to_dto(created)

    async def update_enterprise(
        self, enterprise_id: int, dto: EnterpriseBasicInfoUpdateDTO
    ) -> Optional[EnterpriseBasicInfoDTO]:
        """
        更新企业基础信息
        """
        existing = await self.repository.get_by_id(enterprise_id)
        if not existing:
            return None

        existing.update_info(
            credit_code=dto.credit_code,
            enterprise_name=dto.enterprise_name,
            status=dto.status,
            legal_representative=dto.legal_representative,
            registered_capital=dto.registered_capital,
            establishment_date=dto.establishment_date,
            enterprise_type=dto.enterprise_type,
            registration_authority=dto.registration_authority,
            registered_address=dto.registered_address,
        )

        updated = await self.repository.update(existing)
        logger.info("Updated enterprise basic info: id=%s", enterprise_id)
        return self._entity_to_dto(updated)

    async def get_enterprise(
        self, enterprise_id: int
    ) -> Optional[EnterpriseBasicInfoDTO]:
        """
        根据ID查询企业基础信息
        """
        entity = await self.repository.get_by_id(enterprise_id)
        if not entity:
            return None
        return self._entity_to_dto(entity)

    async def get_enterprise_by_credit_code(
        self, credit_code: str
    ) -> Optional[EnterpriseBasicInfoDTO]:
        """
        根据统一社会信用代码查询企业基础信息
        """
        entity = await self.repository.get_by_credit_code(credit_code)
        if not entity:
            return None
        return self._entity_to_dto(entity)

    async def upsert_enterprise_from_create_dto(
        self, dto: EnterpriseBasicInfoCreateDTO
    ) -> EnterpriseBasicInfoDTO:
        """
        根据统一社会信用代码进行插入或更新（UPSERT）

        - 若该信用代码不存在，则创建新记录
        - 若已存在，则更新对应记录
        """
        existing = await self.repository.get_by_credit_code(dto.credit_code)
        if existing:
            existing.update_info(
                credit_code=dto.credit_code,
                enterprise_name=dto.enterprise_name,
                status=dto.status,
                legal_representative=dto.legal_representative,
                registered_capital=dto.registered_capital,
                establishment_date=dto.establishment_date,
                enterprise_type=dto.enterprise_type,
                registration_authority=dto.registration_authority,
                registered_address=dto.registered_address,
            )
            updated = await self.repository.update(existing)
            logger.info(
                "Upsert enterprise basic info (update): %s", updated.credit_code
            )
            return self._entity_to_dto(updated)

        created = await self.create_enterprise(dto)
        logger.info("Upsert enterprise basic info (create): %s", created.credit_code)
        return created

    async def delete_enterprise(self, enterprise_id: int) -> bool:
        """
        删除企业基础信息
        """
        result = await self.repository.delete(enterprise_id)
        if result:
            logger.info("Deleted enterprise basic info: id=%s", enterprise_id)
        return result

    def _entity_to_dto(self, entity: EnterpriseBasicInfo) -> EnterpriseBasicInfoDTO:
        """将领域实体转换为DTO"""
        if entity.id is None:
            raise ValueError("EnterpriseBasicInfo.id should not be None when mapping to DTO")

        return EnterpriseBasicInfoDTO(
            id=entity.id,
            credit_code=entity.credit_code,
            enterprise_name=entity.enterprise_name,
            status=entity.status,
            legal_representative=entity.legal_representative,
            registered_capital=entity.registered_capital,
            establishment_date=entity.establishment_date,
            enterprise_type=entity.enterprise_type,
            registration_authority=entity.registration_authority,
            registered_address=entity.registered_address,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )



