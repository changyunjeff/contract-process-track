from fastapi import FastAPI
from .register import router_registry, RouterType
from .validator import RouterValidator, TagValidator, PrefixValidator, MetadataValidator, AdminRouteValidator, PrivateRouteValidator


def setup_routers(fastapi_app: FastAPI):
    """
    注册所有路由到FastAPI应用

    使用全局单例路由注册器，支持：
    - 路由类型分类
    - 优先级排序
    - 验证阶段
    """
    # 导入所有API模块，触发路由注册
    # 这确保所有路由在注册前都被添加到注册器中
    # 注意：使用 from ... import 避免覆盖函数参数
    from app import api  # noqa: F401
    from app.api import v1  # noqa: F401

    api_prefix = "/api"

    # 配置验证器（可选）
    # 为API类型路由添加前缀验证
    router_registry.register_validator(
        RouterType.API,
        PrefixValidator(required_prefix=api_prefix)
    )

    # 为管理员路由添加安全验证
    router_registry.register_validator(
        RouterType.ADMIN,
        AdminRouteValidator()
    )

    # 为私有路由添加认证验证
    router_registry.register_validator(
        RouterType.PRIVATE,
        PrivateRouteValidator()
    )

    # 注册所有路由
    stats = router_registry.register_all(fastapi_app)

    return stats

__all__ = [
    'router_registry', 'RouterType',
    'RouterValidator', 'TagValidator', 'PrefixValidator', 'MetadataValidator', 'AdminRouteValidator', 'PrivateRouteValidator',
    "setup_routers"
]