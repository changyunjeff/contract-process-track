"""
全局单例路由注册器
负责管理项目中所有路由的注册，支持路由类型、优先级和验证阶段
"""
from enum import Enum
from typing import Optional, Callable, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from threading import Lock
from fastapi import APIRouter, FastAPI


class RouterType(int, Enum):
    """路由类型枚举（支持位标志组合）"""
    API = 0x0001  # API路由
    PUBLIC = 0x0002  # 公开路由，无需认证
    PRIVATE = 0x0004  # 私有路由，需要认证
    ADMIN = 0x0008  # 管理员路由，需要管理员权限
    INTERNAL = 0x000f  # 内部路由，仅内部服务调用
    WEBHOOK = 0x0010  # Webhook路由

    @classmethod
    def has_type(cls, router_type: int, target_type: 'RouterType') -> bool:
        """
        检查路由类型是否包含目标类型（支持位标志）

        Args:
            router_type: 路由类型（可能是组合值）
            target_type: 目标类型

        Returns:
            bool: 如果 router_type 包含 target_type 则返回 True
        """
        return bool(router_type & target_type.value)


@dataclass
class RouterMetadata:
    """路由元数据"""
    router: APIRouter
    router_type: int  # 路由类型（支持位标志组合，如 RouterType.API | RouterType.PUBLIC）
    priority: int = 100  # 优先级，数字越小优先级越高
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[Any]] = None
    enabled: bool = True  # 是否启用
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


class RouterValidator:
    """路由验证器基类"""

    def validate(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        """
        验证路由是否可以通过注册

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        return True, None


class RouterRegistry:
    """
    全局单例路由注册器

    特性：
    1. 单例模式，确保全局唯一
    2. 支持多种路由类型，不同类型可配置不同的验证器
    3. 支持优先级排序，高优先级路由先注册
    4. 支持验证阶段，路由需通过验证才能注册
    """

    _instance: Optional['RouterRegistry'] = None
    _lock: Lock = Lock()

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化注册器"""
        if self._initialized:
            return

        self._routers: List[RouterMetadata] = []
        self._validators: Dict[int, List[RouterValidator]] = {}  # 使用 int 作为键，支持位标志
        self._type_handlers: Dict[int, Callable[[RouterMetadata, FastAPI], None]] = {}  # 使用 int 作为键
        self._registered_count = 0
        self._skipped_count = 0
        self._failed_count = 0
        # Idempotency tracking
        self._validator_class_names: Dict[int, set[str]] = {}  # 使用 int 作为键
        self._added_router_keys: set[str] = set()
        self._added_router_ids: set[int] = set()
        self._initialized = True

        # 注册默认类型处理器
        self._register_default_handlers()

    def _register_default_handlers(self):
        """注册默认的类型处理器"""
        # 默认处理器：直接注册路由
        def default_handler(metadata: RouterMetadata, fastapi_app: FastAPI) -> None:
            fastapi_app.include_router(metadata.router)

        for router_type in RouterType:
            self._type_handlers[router_type.value] = default_handler

    def register_validator(self, router_type: RouterType, validator: RouterValidator):
        """
        为特定路由类型注册验证器

        Args:
            router_type: 路由类型（单个类型，验证器会应用到包含该类型的所有路由）
            validator: 验证器实例
        """
        type_value = router_type.value if isinstance(router_type, RouterType) else router_type
        if type_value not in self._validators:
            self._validators[type_value] = []
        if type_value not in self._validator_class_names:
            self._validator_class_names[type_value] = set()

        class_name = validator.__class__.__name__
        if class_name in self._validator_class_names[type_value]:
            print(f"⏭️  验证器已存在，跳过: {type_value} -> {class_name}")
            return

        self._validators[type_value].append(validator)
        self._validator_class_names[type_value].add(class_name)
        print(f"✅ 注册验证器: {type_value} -> {class_name}")

    def register_type_handler(
            self,
            router_type: RouterType,
            handler: Callable[[RouterMetadata, FastAPI], None]
    ):
        """
        为特定路由类型注册处理器

        Args:
            router_type: 路由类型（单个类型，处理器会应用到包含该类型的所有路由）
            handler: 处理器函数，接收 (metadata, app) 参数
        """
        type_value = router_type.value if isinstance(router_type, RouterType) else router_type
        self._type_handlers[type_value] = handler
        print(f"✅ 注册类型处理器: {type_value} -> {handler.__name__}")

    def add_router(
            self,
            router: APIRouter,
            router_type: int = RouterType.PUBLIC,  # 支持位标志组合（RouterType 继承自 int）
            priority: int = 100,
            name: Optional[str] = None,
            description: Optional[str] = None,
            enabled: bool = True,
            **metadata
    ) -> bool:
        """
        添加路由到注册队列（尚未注册到FastAPI应用）

        Args:
            router: FastAPI路由对象
            router_type: 路由类型
            priority: 优先级，数字越小优先级越高
            name: 路由名称
            description: 路由描述
            enabled: 是否启用
            **metadata: 额外元数据

        Returns:
            bool: 是否成功添加到队列
        """
        # 去重键：优先使用对象id，其次使用 name|prefix 组合
        dedupe_id = id(router)
        dedupe_key = f"{(name or router.prefix or 'unnamed')}|{getattr(router, 'prefix', '')}"

        if dedupe_id in self._added_router_ids or dedupe_key in self._added_router_keys:
            print(f"⏭️  重复路由，跳过添加: {dedupe_key}")
            return False

        # 确保 router_type 是 int 值（支持位标志组合）
        router_type_value = router_type.value if isinstance(router_type, RouterType) else int(router_type)

        router_metadata = RouterMetadata(
            router=router,
            router_type=router_type_value,
            priority=priority,
            name=name or router.prefix or "unnamed",
            description=description,
            enabled=enabled,
            metadata=metadata
        )

        self._added_router_ids.add(dedupe_id)
        self._added_router_keys.add(dedupe_key)
        self._routers.append(router_metadata)
        # 格式化类型显示（显示所有包含的类型）
        type_names = [t.name for t in RouterType if RouterType.has_type(router_type_value, t)]
        type_display = "|".join(type_names) if type_names else str(router_type_value)
        print(f"📝 路由已添加到注册队列: {router_metadata.name} (类型: {type_display}, 优先级: {priority})")
        return True

    def _validate_router(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        """
        验证路由是否可以通过注册

        Args:
            metadata: 路由元数据

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        # 检查是否启用
        if not metadata.enabled:
            return False, "路由已禁用"

        # 获取所有匹配的验证器（检查路由类型是否包含已注册的验证器类型）
        all_validators = []
        for validator_type, validators in self._validators.items():
            if RouterType.has_type(metadata.router_type, RouterType(validator_type)):
                all_validators.extend(validators)

        # 执行所有匹配的验证器
        for validator in all_validators:
            is_valid, error_msg = validator.validate(metadata)
            if not is_valid:
                return False, error_msg

        return True, None

    def _register_router(self, metadata: RouterMetadata, app: FastAPI) -> bool:
        """
        注册单个路由到FastAPI应用

        Args:
            metadata: 路由元数据
            app: FastAPI应用实例

        Returns:
            bool: 是否注册成功
        """
        # 验证路由
        is_valid, error_msg = self._validate_router(metadata)
        if not is_valid:
            print(f"❌ 路由验证失败: {metadata.name} - {error_msg}")
            self._failed_count += 1
            return False

        # 获取类型处理器（按优先级查找：优先使用最具体的类型处理器）
        handler = None
        # 按优先级顺序查找处理器（从最具体的类型开始）
        priority_order = [RouterType.ADMIN, RouterType.PRIVATE, RouterType.API, RouterType.PUBLIC, RouterType.WEBHOOK,
                          RouterType.INTERNAL]
        for router_type in priority_order:
            if RouterType.has_type(metadata.router_type, router_type):
                handler = self._type_handlers.get(router_type.value)
                if handler:
                    break

        # 如果没找到，使用默认处理器
        if handler is None:
            def default_handler(metadata: RouterMetadata, fastapi_app: FastAPI) -> None:
                fastapi_app.include_router(metadata.router)
            handler = default_handler
            type_names = [t.name for t in RouterType if RouterType.has_type(metadata.router_type, t)]
            type_display = "|".join(type_names) if type_names else str(metadata.router_type)
            print(f"⚠️  未找到类型处理器: {type_display}，使用默认处理器")

        try:
            # 执行类型特定的注册逻辑
            handler(metadata, app)
            type_names = [t.name for t in RouterType if RouterType.has_type(metadata.router_type, t)]
            type_display = "|".join(type_names) if type_names else str(metadata.router_type)
            print(f"✅ 路由注册成功: {metadata.name} (类型: {type_display}, 优先级: {metadata.priority})")
            self._registered_count += 1
            return True
        except Exception as e:
            print(f"❌ 路由注册异常: {metadata.name} - {str(e)}")
            self._failed_count += 1
            return False

    def register_all(self, app: FastAPI) -> Dict[str, int]:
        """
        将所有路由注册到FastAPI应用

        按照优先级排序，高优先级（数字小）先注册

        Args:
            app: FastAPI应用实例

        Returns:
            Dict: 注册统计信息
        """
        print("\n" + "=" * 60)
        print("🚀 开始注册路由...")
        print("=" * 60)

        # 重置计数器
        self._registered_count = 0
        self._skipped_count = 0
        self._failed_count = 0

        # 按优先级排序（优先级数字越小，优先级越高）
        sorted_routers = sorted(self._routers, key=lambda x: (x.priority, x.name))

        # 注册所有路由
        for metadata in sorted_routers:
            if not metadata.enabled:
                print(f"⏭️  跳过已禁用的路由: {metadata.name}")
                self._skipped_count += 1
                continue

            self._register_router(metadata, app)

        # 打印统计信息
        print("=" * 60)
        print(f"📊 路由注册统计:")
        print(f"   ✅ 成功注册: {self._registered_count}")
        print(f"   ⏭️  跳过: {self._skipped_count}")
        print(f"   ❌ 失败: {self._failed_count}")
        print(f"   📝 总计: {len(self._routers)}")
        print("=" * 60 + "\n")

        return {
            "registered": self._registered_count,
            "skipped": self._skipped_count,
            "failed": self._failed_count,
            "total": len(self._routers)
        }

    def clear(self):
        """清空所有已注册的路由（用于测试）"""
        self._routers.clear()
        self._registered_count = 0
        self._skipped_count = 0
        self._failed_count = 0
        print("🗑️  已清空所有路由")

    def get_statistics(self) -> Dict[str, Any]:
        """获取注册器统计信息"""
        # 统计每个类型的路由数量（支持位标志）
        by_type = {}
        for router_type in RouterType:
            count = sum(1 for r in self._routers if RouterType.has_type(r.router_type, router_type))
            by_type[router_type.value] = count

        return {
            "total_routers": len(self._routers),
            "registered": self._registered_count,
            "skipped": self._skipped_count,
            "failed": self._failed_count,
            "by_type": by_type
        }


# 全局单例实例
router_registry = RouterRegistry()