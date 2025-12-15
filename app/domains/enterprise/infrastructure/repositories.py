"""
PostgreSQL 工商企业基础信息仓储实现

基础设施层实现，负责与 PostgreSQL 交互
"""
from __future__ import annotations

import logging
from typing import Optional, Mapping, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..domain.entities import EnterpriseBasicInfo
from ..domain.repositories import IEnterpriseBasicInfoRepository
from app.services.postgres_service import get_async_session_factory
from app.tools import datetime_to_timestamp_ms


logger = logging.getLogger(__name__)


class PostgresEnterpriseBasicInfoRepository(IEnterpriseBasicInfoRepository):
    """基于 PostgreSQL 的企业基础信息仓储实现"""

    def __init__(self) -> None:
        self._session_factory: async_sessionmaker[AsyncSession] = (
            get_async_session_factory()
        )

    async def _row_to_entity(self, row: Mapping[str, Any]) -> EnterpriseBasicInfo:
        """
        将数据库行转换为领域实体

        - 数据库中的 created_at / updated_at 为 TIMESTAMP
        - 领域实体中使用毫秒级时间戳（int）
        """
        created_at_dt = row["created_at"]
        updated_at_dt = row["updated_at"]

        return EnterpriseBasicInfo(
            id=row["id"],
            credit_code=row["credit_code"],
            enterprise_name=row["enterprise_name"],
            status=row["status"],
            legal_representative=row.get("legal_representative"),
            registered_capital=row.get("registered_capital"),
            establishment_date=row.get("establishment_date"),
            enterprise_type=row.get("enterprise_type"),
            registration_authority=row.get("registration_authority"),
            registered_address=row.get("registered_address"),
            created_at=datetime_to_timestamp_ms(created_at_dt),
            updated_at=datetime_to_timestamp_ms(updated_at_dt),
        )

    async def create(self, enterprise: EnterpriseBasicInfo) -> EnterpriseBasicInfo:
        """创建企业基础信息"""
        async with self._session_factory() as session:
            stmt = text(
                """
                INSERT INTO enterprise_basic_info (
                    credit_code,
                    enterprise_name,
                    status,
                    legal_representative,
                    registered_capital,
                    establishment_date,
                    enterprise_type,
                    registration_authority,
                    registered_address
                ) VALUES (
                    :credit_code,
                    :enterprise_name,
                    :status,
                    :legal_representative,
                    :registered_capital,
                    :establishment_date,
                    :enterprise_type,
                    :registration_authority,
                    :registered_address
                )
                RETURNING
                    id,
                    credit_code,
                    enterprise_name,
                    status,
                    legal_representative,
                    registered_capital,
                    establishment_date,
                    enterprise_type,
                    registration_authority,
                    registered_address,
                    created_at,
                    updated_at
                """
            )
            params = {
                "credit_code": enterprise.credit_code,
                "enterprise_name": enterprise.enterprise_name,
                "status": enterprise.status,
                "legal_representative": enterprise.legal_representative,
                "registered_capital": enterprise.registered_capital,
                "establishment_date": enterprise.establishment_date,
                "enterprise_type": enterprise.enterprise_type,
                "registration_authority": enterprise.registration_authority,
                "registered_address": enterprise.registered_address,
            }
            result = await session.execute(stmt, params)
            await session.commit()
            row = result.mappings().one()
            created = await self._row_to_entity(row)
            logger.info(
                "Inserted enterprise_basic_info: id=%s, credit_code=%s",
                created.id,
                created.credit_code,
            )
            return created

    async def update(self, enterprise: EnterpriseBasicInfo) -> EnterpriseBasicInfo:
        """更新企业基础信息"""
        if enterprise.id is None:
            raise ValueError("enterprise.id is required for update")

        async with self._session_factory() as session:
            stmt = text(
                """
                UPDATE enterprise_basic_info
                SET
                    credit_code = :credit_code,
                    enterprise_name = :enterprise_name,
                    status = :status,
                    legal_representative = :legal_representative,
                    registered_capital = :registered_capital,
                    establishment_date = :establishment_date,
                    enterprise_type = :enterprise_type,
                    registration_authority = :registration_authority,
                    registered_address = :registered_address,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                RETURNING
                    id,
                    credit_code,
                    enterprise_name,
                    status,
                    legal_representative,
                    registered_capital,
                    establishment_date,
                    enterprise_type,
                    registration_authority,
                    registered_address,
                    created_at,
                    updated_at
                """
            )
            params = {
                "id": enterprise.id,
                "credit_code": enterprise.credit_code,
                "enterprise_name": enterprise.enterprise_name,
                "status": enterprise.status,
                "legal_representative": enterprise.legal_representative,
                "registered_capital": enterprise.registered_capital,
                "establishment_date": enterprise.establishment_date,
                "enterprise_type": enterprise.enterprise_type,
                "registration_authority": enterprise.registration_authority,
                "registered_address": enterprise.registered_address,
            }
            result = await session.execute(stmt, params)
            await session.commit()
            row = result.mappings().one()
            updated = await self._row_to_entity(row)
            logger.info(
                "Updated enterprise_basic_info: id=%s, credit_code=%s",
                updated.id,
                updated.credit_code,
            )
            return updated

    async def get_by_id(self, enterprise_id: int) -> Optional[EnterpriseBasicInfo]:
        """根据ID查询企业基础信息"""
        async with self._session_factory() as session:
            stmt = text(
                """
                SELECT
                    id,
                    credit_code,
                    enterprise_name,
                    status,
                    legal_representative,
                    registered_capital,
                    establishment_date,
                    enterprise_type,
                    registration_authority,
                    registered_address,
                    created_at,
                    updated_at
                FROM enterprise_basic_info
                WHERE id = :id
                """
            )
            result = await session.execute(stmt, {"id": enterprise_id})
            row = result.mappings().one_or_none()
            if row is None:
                return None
            return await self._row_to_entity(row)

    async def get_by_credit_code(
        self, credit_code: str
    ) -> Optional[EnterpriseBasicInfo]:
        """根据统一社会信用代码查询企业基础信息"""
        async with self._session_factory() as session:
            stmt = text(
                """
                SELECT
                    id,
                    credit_code,
                    enterprise_name,
                    status,
                    legal_representative,
                    registered_capital,
                    establishment_date,
                    enterprise_type,
                    registration_authority,
                    registered_address,
                    created_at,
                    updated_at
                FROM enterprise_basic_info
                WHERE credit_code = :credit_code
                """
            )
            result = await session.execute(stmt, {"credit_code": credit_code})
            row = result.mappings().one_or_none()
            if row is None:
                return None
            return await self._row_to_entity(row)

    async def delete(self, enterprise_id: int) -> bool:
        """删除企业基础信息"""
        async with self._session_factory() as session:
            stmt = text(
                """
                DELETE FROM enterprise_basic_info
                WHERE id = :id
                """
            )
            result = await session.execute(stmt, {"id": enterprise_id})
            await session.commit()
            deleted = result.rowcount or 0
            logger.info(
                "Deleted enterprise_basic_info: id=%s, affected_rows=%s",
                enterprise_id,
                deleted,
            )
            return deleted > 0



