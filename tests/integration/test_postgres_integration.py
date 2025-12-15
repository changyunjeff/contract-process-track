"""
Integration tests for PostgreSQL service.

These tests require a running PostgreSQL instance.
Use pytest markers to control integration tests:
    pytest -m "not integration"      # Skip integration tests
    pytest -m integration            # Run only integration tests
"""
import os

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.configs.postgres_config import PostgresConfig
from app.services.postgres_service import PostgresService


@pytest.fixture
def postgres_config() -> PostgresConfig:
    """Fixture for PostgreSQL configuration.

    Uses environment variables if provided, otherwise falls back to config.test.yaml defaults:
        host=postgres, port=5432, database=company_info_cn, user=admin
    Password is taken from POSTGRES_PASSWORD if not given explicitly.
    """
    return PostgresConfig(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "company_info_cn"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD"),
        echo=False,
    )


@pytest_asyncio.fixture
async def postgres_service(postgres_config: PostgresConfig):
    """Fixture for PostgreSQL service."""
    service = PostgresService(postgres_config)
    service.init_engine()
    try:
        yield service
    finally:
        await service.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
class TestPostgresIntegration:
    """Integration tests for PostgreSQL service."""

    async def test_postgres_connection(self, postgres_service: PostgresService):
        """Test basic PostgreSQL connection by executing SELECT 1."""
        engine = postgres_service.engine
        if engine is None:
            pytest.skip("PostgreSQL engine not initialized")

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar_one()
            assert value == 1

    async def test_postgres_simple_query(self, postgres_service: PostgresService):
        """Test a simple transaction using a session."""
        engine = postgres_service.engine
        if engine is None:
            pytest.skip("PostgreSQL engine not initialized")

        Session = postgres_service.get_session_factory()
        async with Session() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar_one()
            assert isinstance(db_name, str)
            assert db_name != ""


