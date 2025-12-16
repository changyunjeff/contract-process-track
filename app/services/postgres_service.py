from __future__ import annotations

import logging
import os
from typing import Optional, AsyncIterator, Dict

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_postgres_config, get_all_database_configs
from app.configs import PostgresConfig


logger = logging.getLogger(__name__)

# 存储多个数据库服务的字典，key 为数据库名称
_pg_services: Dict[str, PostgresService] = {}


class PostgresService:
    """PostgreSQL connection service using SQLAlchemy async engine."""

    def __init__(self, config: Optional[PostgresConfig] = None) -> None:
        self.config = config or get_postgres_config()
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def _build_dsn(self) -> str:
        if self.config is None:
            raise RuntimeError("PostgreSQL configuration not found")

        password = self.config.password or os.getenv("POSTGRES_PASSWORD", "")
        if password:
            logger.debug(f"🔐 Using PostgreSQL password (length: {len(password)})")
        else:
            logger.warning(
                "⚠️ No PostgreSQL password configured - connection may fail if the server requires authentication"
            )

        # asyncpg driver DSN
        return (
            f"postgresql+asyncpg://{self.config.user}:{password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
        )

    def init_engine(self) -> None:
        """Create SQLAlchemy async engine and session factory."""
        if self.config is None:
            logger.warning("PostgreSQL configuration not found, skipping engine initialization")
            return

        if self._engine is not None:
            return

        dsn = self._build_dsn()
        self._engine = create_async_engine(
            dsn,
            echo=self.config.echo,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            future=True,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        logger.info(
            "✅ PostgreSQL async engine initialized "
            f"for {self.config.user}@{self.config.host}:{self.config.port}/{self.config.database}"
        )

    async def dispose(self) -> None:
        """Dispose engine and close all connections."""
        if self._engine is not None:
            try:
                await self._engine.dispose()
                logger.info("✅ PostgreSQL engine disposed")
            except SQLAlchemyError as exc:
                logger.error(f"❌ Error disposing PostgreSQL engine: {exc}")
            finally:
                self._engine = None
                self._session_factory = None

    @property
    def engine(self) -> Optional[AsyncEngine]:
        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("PostgreSQL session factory not initialized")
        return self._session_factory

    async def session(self) -> AsyncIterator[AsyncSession]:
        """Async context manager style session generator."""
        if self._session_factory is None:
            raise RuntimeError("PostgreSQL session factory not initialized")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def init_postgres_service(
    config: Optional[PostgresConfig] = None, 
    db_name: Optional[str] = None
) -> PostgresService:
    """
    Initialize PostgreSQL service and engine for a specific database.
    
    Args:
        config: Optional PostgresConfig. If None, will load from config file.
        db_name: Database name (e.g., 'company_info_cn', 'law_cn'). 
                 If None and config is None, will initialize all databases from config.
    
    Returns:
        PostgresService instance
    """
    global _pg_services
    
    if config is not None:
        # 如果提供了 config，使用它
        if db_name is None:
            db_name = config.database or 'default'
        
        if db_name not in _pg_services:
            service = PostgresService(config)
            service.init_engine()
            _pg_services[db_name] = service
        return _pg_services[db_name]
    
    # 如果没有提供 config，从配置文件加载
    if db_name:
        # 初始化指定的数据库
        config = get_postgres_config(db_name)
        if config is None:
            raise ValueError(f"Database configuration not found for: {db_name}")
        
        if db_name not in _pg_services:
            service = PostgresService(config)
            service.init_engine()
            _pg_services[db_name] = service
        return _pg_services[db_name]
    else:
        # 初始化所有配置的数据库
        all_configs = get_all_database_configs()
        if not all_configs:
            logger.warning("No database configurations found")
            return None
        
        for name, cfg in all_configs.items():
            if name not in _pg_services:
                service = PostgresService(cfg)
                service.init_engine()
                _pg_services[name] = service
                logger.info(f"Initialized database service: {name}")
        
        # 返回第一个服务（向后兼容）
        if _pg_services:
            return next(iter(_pg_services.values()))
        return None


async def close_postgres_service(db_name: Optional[str] = None) -> None:
    """
    Dispose PostgreSQL service engine(s).
    
    Args:
        db_name: Database name. If None, closes all database services.
    """
    global _pg_services
    
    if db_name:
        if db_name in _pg_services:
            await _pg_services[db_name].dispose()
            del _pg_services[db_name]
            logger.info(f"Closed database service: {db_name}")
    else:
        # 关闭所有数据库服务
        for name, service in list(_pg_services.items()):
            await service.dispose()
            logger.info(f"Closed database service: {name}")
        _pg_services.clear()


def get_postgres_service(db_name: Optional[str] = None) -> Optional[PostgresService]:
    """
    Get PostgreSQL service instance.
    
    Args:
        db_name: Database name. If None, returns the first available service.
    
    Returns:
        PostgresService instance or None
    """
    if db_name:
        return _pg_services.get(db_name)
    
    # 向后兼容：返回第一个服务
    if _pg_services:
        return next(iter(_pg_services.values()))
    return None


def get_async_session_factory(db_name: Optional[str] = None) -> async_sessionmaker[AsyncSession]:
    """
    Shortcut for getting async session factory.
    
    Args:
        db_name: Database name. If None, uses the first available service.
    
    Returns:
        async_sessionmaker instance
    """
    service = get_postgres_service(db_name)
    if service is None:
        if db_name:
            raise RuntimeError(f"PostgreSQL service not initialized for database: {db_name}")
        raise RuntimeError("PostgreSQL service not initialized")
    return service.get_session_factory()


