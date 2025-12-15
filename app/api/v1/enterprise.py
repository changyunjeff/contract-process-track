"""
工商企业基础信息 API 路由（v1版本）

表现层，处理HTTP请求和响应
"""
from __future__ import annotations

import csv
from datetime import date
from io import StringIO
from typing import List

from fastapi import APIRouter, UploadFile, File
from sqlalchemy.exc import IntegrityError

from app.models import HttpResponse
from app.exceptions import (
    NotFoundException,
    BadRequestException,
    ServerUnavailableException,
    InternalServerException,
)
from app.domains.enterprise.application.services import (
    EnterpriseBasicInfoApplicationService,
)
from app.domains.enterprise.application.dto import (
    EnterpriseBasicInfoCreateDTO,
    EnterpriseBasicInfoUpdateDTO,
    EnterpriseBasicInfoDTO,
)
from app.domains.enterprise.infrastructure.repositories import (
    PostgresEnterpriseBasicInfoRepository,
)


enterprise_router = APIRouter(
    prefix="/api/v1/enterprise", tags=["enterprise-basic-info"]
)


def get_enterprise_service() -> EnterpriseBasicInfoApplicationService:
    """获取企业基础信息应用服务实例（依赖注入）"""
    from app.services.postgres_service import get_postgres_service

    pg_service = get_postgres_service()
    if pg_service is None or pg_service.engine is None:
        raise RuntimeError("PostgreSQL service is not available")

    repository = PostgresEnterpriseBasicInfoRepository()
    return EnterpriseBasicInfoApplicationService(repository)


@enterprise_router.post(
    "/basic-info",
    response_model=HttpResponse[EnterpriseBasicInfoDTO],
)
async def create_enterprise_basic_info(
    data: EnterpriseBasicInfoCreateDTO,
) -> HttpResponse[EnterpriseBasicInfoDTO]:
    """
    创建工商企业基础信息
    """
    try:
        service = get_enterprise_service()
        created = await service.create_enterprise(data)
        return HttpResponse.success(data=created, msg="企业基础信息创建成功")
    except IntegrityError:
        # 违反唯一约束（如 credit_code 已存在）
        raise BadRequestException(
            f"企业基础信息创建失败：统一社会信用代码已存在（credit_code={data.credit_code}）"
        )
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"创建企业基础信息失败: {str(e)}")


@enterprise_router.put(
    "/basic-info/{enterprise_id}",
    response_model=HttpResponse[EnterpriseBasicInfoDTO],
)
async def update_enterprise_basic_info(
    enterprise_id: int,
    data: EnterpriseBasicInfoUpdateDTO,
) -> HttpResponse[EnterpriseBasicInfoDTO]:
    """
    更新工商企业基础信息
    """
    try:
        service = get_enterprise_service()
        updated = await service.update_enterprise(enterprise_id, data)
        if updated is None:
            raise NotFoundException(f"企业基础信息不存在: {enterprise_id}")
        return HttpResponse.success(data=updated, msg="企业基础信息更新成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"更新企业基础信息失败: {str(e)}")


@enterprise_router.get(
    "/basic-info/{enterprise_id}",
    response_model=HttpResponse[EnterpriseBasicInfoDTO],
)
async def get_enterprise_basic_info(
    enterprise_id: int,
) -> HttpResponse[EnterpriseBasicInfoDTO]:
    """
    根据ID查询工商企业基础信息
    """
    try:
        service = get_enterprise_service()
        enterprise = await service.get_enterprise(enterprise_id)
        if enterprise is None:
            raise NotFoundException(f"企业基础信息不存在: {enterprise_id}")
        return HttpResponse.success(data=enterprise, msg="查询成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"查询企业基础信息失败: {str(e)}")


@enterprise_router.get(
    "/basic-info/by-credit/{credit_code}",
    response_model=HttpResponse[EnterpriseBasicInfoDTO],
)
async def get_enterprise_basic_info_by_credit_code(
    credit_code: str,
) -> HttpResponse[EnterpriseBasicInfoDTO]:
    """
    根据统一社会信用代码查询工商企业基础信息
    """
    try:
        service = get_enterprise_service()
        enterprise = await service.get_enterprise_by_credit_code(credit_code)
        if enterprise is None:
            raise NotFoundException(f"企业基础信息不存在: {credit_code}")
        return HttpResponse.success(data=enterprise, msg="查询成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"查询企业基础信息失败: {str(e)}")


@enterprise_router.delete(
    "/basic-info/{enterprise_id}",
    response_model=HttpResponse[bool],
)
async def delete_enterprise_basic_info(
    enterprise_id: int,
) -> HttpResponse[bool]:
    """
    删除工商企业基础信息
    """
    try:
        service = get_enterprise_service()
        deleted = await service.delete_enterprise(enterprise_id)
        if not deleted:
            raise NotFoundException(f"企业基础信息不存在: {enterprise_id}")
        return HttpResponse.success(data=True, msg="企业基础信息删除成功")
    except NotFoundException:
        raise
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")
    except Exception as e:  # noqa: BLE001
        raise InternalServerException(f"删除企业基础信息失败: {str(e)}")


@enterprise_router.post(
    "/basic-info/upload-csv",
    response_model=HttpResponse[List[EnterpriseBasicInfoDTO]],
)
async def upload_enterprise_basic_info_csv(
    file: UploadFile = File(..., description="包含企业基础信息的CSV文件"),
) -> HttpResponse[List[EnterpriseBasicInfoDTO]]:
    """
    通过上传CSV文件批量插入或更新企业基础信息（按统一社会信用代码UPSERT）

    期望CSV表头包含以下字段（区分大小写）：
    - credit_code（必填）
    - enterprise_name（必填）
    - status（必填）
    - legal_representative
    - registered_capital
    - establishment_date（可选，格式为YYYY-MM-DD）
    - enterprise_type
    - registration_authority
    - registered_address
    """
    if not file.filename.lower().endswith(".csv"):
        raise BadRequestException("仅支持上传 CSV 文件")

    try:
        service = get_enterprise_service()
    except RuntimeError as e:
        raise ServerUnavailableException(f"PostgreSQL服务不可用: {str(e)}")

    try:
        content_bytes = await file.read()
        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # 尝试常见的 GBK 编码
            content = content_bytes.decode("gbk")
    except Exception as e:  # noqa: BLE001
        raise BadRequestException(f"读取上传文件失败: {str(e)}")

    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise BadRequestException("CSV 文件缺少表头")

    processed: List[EnterpriseBasicInfoDTO] = []

    for index, row in enumerate(reader, start=2):  # 从第2行开始（第1行为表头）
        credit_code = (row.get("credit_code") or "").strip()
        enterprise_name = (row.get("enterprise_name") or "").strip()
        status = (row.get("status") or "").strip()

        if not credit_code or not enterprise_name or not status:
            # 基础必填字段缺失，直接报错并指出行号
            raise BadRequestException(
                f"第 {index} 行缺少必填字段：credit_code / enterprise_name / status"
            )

        raw_date = (row.get("establishment_date") or "").strip() or None
        parsed_date: date | None = None
        if raw_date:
            try:
                parsed_date = date.fromisoformat(raw_date)
            except ValueError:
                raise BadRequestException(
                    f"第 {index} 行成立日期格式错误，应为 YYYY-MM-DD，实际为: {raw_date}"
                )

        dto = EnterpriseBasicInfoCreateDTO(
            credit_code=credit_code,
            enterprise_name=enterprise_name,
            status=status,
            legal_representative=(row.get("legal_representative") or "").strip() or None,
            registered_capital=(row.get("registered_capital") or "").strip() or None,
            establishment_date=parsed_date,
            enterprise_type=(row.get("enterprise_type") or "").strip() or None,
            registration_authority=(
                row.get("registration_authority") or ""
            ).strip() or None,
            registered_address=(row.get("registered_address") or "").strip() or None,
        )

        try:
            result = await service.upsert_enterprise_from_create_dto(dto)
            processed.append(result)
        except Exception as e:  # noqa: BLE001
            # 精确到行号，便于快速发现问题数据
            raise InternalServerException(
                f"处理第 {index} 行数据时发生错误: {str(e)}"
            ) from e

    return HttpResponse.success(
        data=processed,
        msg=f"CSV 导入成功，处理记录数: {len(processed)}",
    )



