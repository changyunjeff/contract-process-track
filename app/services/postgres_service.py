from __future__ import annotations

import logging
import os
from typing import Optional, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_postgres_config
from app.configs import PostgresConfig


logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


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


_pg_service: Optional[PostgresService] = None


def init_postgres_service(config: Optional[PostgresConfig] = None) -> PostgresService:
    """Initialize global PostgreSQL service and engine."""
    global _pg_service
    if _pg_service is None:
        _pg_service = PostgresService(config)
        _pg_service.init_engine()
    return _pg_service


async def close_postgres_service() -> None:
    """Dispose global PostgreSQL service engine."""
    global _pg_service
    if _pg_service is not None:
        await _pg_service.dispose()
        _pg_service = None


def get_postgres_service() -> Optional[PostgresService]:
    """Get global PostgreSQL service instance."""
    return _pg_service


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Shortcut for getting global async session factory."""
    service = get_postgres_service()
    if service is None:
        raise RuntimeError("PostgreSQL service not initialized")
    return service.get_session_factory()


