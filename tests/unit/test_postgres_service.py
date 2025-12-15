"""
Unit tests for PostgreSQL service.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.configs.postgres_config import PostgresConfig
from app.services.postgres_service import (
    PostgresService,
    init_postgres_service,
    close_postgres_service,
    get_postgres_service,
    get_async_session_factory,
)


@pytest.mark.unit
class TestPostgresService:
    """Test PostgreSQL service."""

    def test_postgres_service_init_with_config(self):
        """Test Postgres service initialization with config."""
        config = PostgresConfig(host="postgres", port=5432, database="db", user="user")
        service = PostgresService(config)
        assert service.config == config
        assert service.engine is None

    def test_postgres_service_init_without_config(self):
        """Test Postgres service initialization without config."""
        with patch("app.services.postgres_service.get_postgres_config", return_value=None):
            service = PostgresService()
            assert service.config is None

    def test_build_dsn_with_password_from_config(self):
        """Test DSN building with password from config."""
        config = PostgresConfig(
            host="postgres",
            port=5432,
            database="db",
            user="user",
            password="secret",
        )
        service = PostgresService(config)
        dsn = service._build_dsn()
        assert dsn == "postgresql+asyncpg://user:secret@postgres:5432/db"

    def test_build_dsn_with_password_from_env(self, monkeypatch):
        """Test DSN building with password from environment."""
        config = PostgresConfig(
            host="postgres",
            port=5432,
            database="db",
            user="user",
            password=None,
        )
        service = PostgresService(config)
        monkeypatch.setenv("POSTGRES_PASSWORD", "env_secret")
        dsn = service._build_dsn()
        assert dsn == "postgresql+asyncpg://user:env_secret@postgres:5432/db"

    def test_build_dsn_without_password_raises_warning(self, caplog, monkeypatch):
        """Test DSN building without password logs warning."""
        config = PostgresConfig(
            host="postgres",
            port=5432,
            database="db",
            user="user",
            password=None,
        )
        service = PostgresService(config)
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

        with caplog.at_level("WARNING"):
            dsn = service._build_dsn()

        assert "No PostgreSQL password configured" in caplog.text
        assert dsn == "postgresql+asyncpg://user:@postgres:5432/db"

    def test_init_engine_creates_engine_and_session_factory(self):
        """Test that init_engine creates engine and session factory."""
        config = PostgresConfig(
            host="postgres",
            port=5432,
            database="db",
            user="user",
            password="secret",
        )
        service = PostgresService(config)

        mock_engine = MagicMock()
        mock_sessionmaker = MagicMock()

        with patch(
            "app.services.postgres_service.create_async_engine",
            return_value=mock_engine,
        ) as create_engine_mock, patch(
            "app.services.postgres_service.async_sessionmaker",
            return_value=mock_sessionmaker,
        ) as sessionmaker_mock:
            service.init_engine()

        create_engine_mock.assert_called_once()
        sessionmaker_mock.assert_called_once()
        assert service.engine is mock_engine
        assert service.get_session_factory() is mock_sessionmaker

    def test_init_engine_with_no_config_logs_warning(self, caplog):
        """Test init_engine when config is None."""
        with patch("app.services.postgres_service.get_postgres_config", return_value=None):
            service = PostgresService()
            with caplog.at_level("WARNING"):
                service.init_engine()
            assert "PostgreSQL configuration not found" in caplog.text

    @pytest.mark.asyncio
    async def test_dispose_engine(self):
        """Test dispose closes engine and clears session factory."""
        config = PostgresConfig()
        service = PostgresService(config)

        mock_engine = AsyncMock()
        service._engine = mock_engine
        service._session_factory = MagicMock()

        await service.dispose()

        mock_engine.dispose.assert_awaited_once()
        assert service.engine is None
        with pytest.raises(RuntimeError):
            service.get_session_factory()

    def test_get_session_factory_not_initialized(self):
        """Test get_session_factory raises when not initialized."""
        config = PostgresConfig()
        service = PostgresService(config)
        with pytest.raises(RuntimeError, match="PostgreSQL session factory not initialized"):
            service.get_session_factory()

    @pytest.mark.asyncio
    async def test_session_context_manager(self):
        """Test session async context manager behavior."""
        config = PostgresConfig()
        service = PostgresService(config)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        # sessionmaker 是一个可调用对象，返回 AsyncSession；这里用同步工厂模拟
        def session_factory():
            return mock_session

        service._session_factory = session_factory  # type: ignore[assignment]

        async for _ in service.session():
            pass

        mock_session.commit.assert_awaited_once()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_session_context_manager_rollback_on_error(self):
        """Test session async context manager rolls back on error."""
        config = PostgresConfig()
        service = PostgresService(config)

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        def session_factory():
            return mock_session

        service._session_factory = session_factory  # type: ignore[assignment]

        class TestError(Exception):
            pass

        # 显式驱动 async 生成器，并注入异常，确保触发 rollback 分支
        gen = service.session()
        # 先进入一次生成器，获取 session
        _ = await gen.__anext__()

        with pytest.raises(TestError):
            await gen.athrow(TestError("boom"))

        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()


@pytest.mark.unit
class TestGlobalPostgresService:
    """Test global Postgres service helpers."""

    def setup_method(self):
        # Ensure clean state before each test
        from app import services as _  # noqa: F401  # ensure package imported
        import app.services.postgres_service as pg_mod

        pg_mod._pg_service = None

    def test_init_postgres_service_and_getters(self):
        """Test init_postgres_service, get_postgres_service, get_async_session_factory."""
        config = PostgresConfig()
        mock_service = MagicMock()
        mock_session_factory = MagicMock()
        mock_service.get_session_factory.return_value = mock_session_factory

        with patch(
            "app.services.postgres_service.PostgresService",
            return_value=mock_service,
        ) as service_cls:
            service = init_postgres_service(config)

        service_cls.assert_called_once_with(config)
        assert service is mock_service
        assert get_postgres_service() is mock_service
        assert get_async_session_factory() is mock_session_factory

    @pytest.mark.asyncio
    async def test_close_postgres_service(self, monkeypatch):
        """Test close_postgres_service disposes global service."""
        import app.services.postgres_service as pg_mod

        mock_service = MagicMock()
        mock_service.dispose = AsyncMock()

        # 直接把全局 _pg_service 设为我们的 mock
        monkeypatch.setattr(pg_mod, "_pg_service", mock_service, raising=False)

        await close_postgres_service()
        mock_service.dispose.assert_awaited_once()

    def test_get_async_session_factory_without_service_raises(self):
        """Test get_async_session_factory raises when service not initialized."""
        with patch("app.services.postgres_service._pg_service", None):
            with pytest.raises(RuntimeError, match="PostgreSQL service not initialized"):
                get_async_session_factory()


