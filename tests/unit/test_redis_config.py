"""
Unit tests for Redis configuration.
"""
import pytest
from app.configs.redis_config import RedisConfig


@pytest.mark.unit
class TestRedisConfig:
    """Test Redis configuration model."""

    def test_redis_config_defaults(self):
        """Test Redis config with default values."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.decode_responses is True
        assert config.socket_timeout == 5
        assert config.socket_connect_timeout == 5
        assert config.retry_on_timeout is True
        assert config.health_check_interval == 30

    def test_redis_config_custom_values(self):
        """Test Redis config with custom values."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="test_password",
            decode_responses=False,
            socket_timeout=10,
            socket_connect_timeout=10,
            retry_on_timeout=False,
            health_check_interval=60,
        )
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "test_password"
        assert config.decode_responses is False
        assert config.socket_timeout == 10
        assert config.socket_connect_timeout == 10
        assert config.retry_on_timeout is False
        assert config.health_check_interval == 60

    def test_redis_config_optional_password(self):
        """Test Redis config with optional password."""
        config = RedisConfig(host="localhost", port=6379)
        assert config.password is None

        config_with_password = RedisConfig(host="localhost", port=6379, password="secret")
        assert config_with_password.password == "secret"

