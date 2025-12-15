"""
Unit tests for PostgreSQL configuration.
"""
import pytest

from app.configs.postgres_config import PostgresConfig


@pytest.mark.unit
class TestPostgresConfig:
    """Test PostgreSQL configuration model."""

    def test_postgres_config_defaults(self):
        """Test Postgres config with default values."""
        config = PostgresConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "process_track"
        assert config.user == "postgres"
        assert config.password is None
        assert config.echo is False
        assert config.pool_size == 5
        assert config.max_overflow == 10

    def test_postgres_config_custom_values(self):
        """Test Postgres config with custom values."""
        config = PostgresConfig(
            host="postgres",
            port=5433,
            database="custom_db",
            user="custom_user",
            password="secret",
            echo=True,
            pool_size=10,
            max_overflow=20,
        )

        assert config.host == "postgres"
        assert config.port == 5433
        assert config.database == "custom_db"
        assert config.user == "custom_user"
        assert config.password == "secret"
        assert config.echo is True
        assert config.pool_size == 10
        assert config.max_overflow == 20


