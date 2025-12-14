"""
Unit tests for Redis service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.redis_service import RedisService
from app.configs.redis_config import RedisConfig


@pytest.mark.unit
class TestRedisService:
    """Test Redis service."""

    def test_redis_service_init_with_config(self):
        """Test Redis service initialization with config."""
        config = RedisConfig(host="localhost", port=6379)
        service = RedisService(config)
        assert service.config == config
        assert service._client is None
        assert service.is_connected() is False

    def test_redis_service_init_without_config(self):
        """Test Redis service initialization without config."""
        with patch("app.services.redis_service.get_redis_config", return_value=None):
            service = RedisService()
            assert service.config is None

    @pytest.mark.asyncio
    async def test_redis_service_connect_success(self):
        """Test successful Redis connection."""
        config = RedisConfig(host="localhost", port=6379)
        service = RedisService(config)

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()

        with patch("app.services.redis_service.aioredis.from_url", return_value=mock_client):
            await service.connect()
            assert service.is_connected() is True
            assert service.client == mock_client
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_service_connect_with_password_from_env(self):
        """Test Redis connection with password from environment."""
        config = RedisConfig(host="localhost", port=6379, password=None)
        service = RedisService(config)

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("app.services.redis_service.aioredis.from_url", return_value=mock_client), \
             patch("os.getenv", return_value="env_password"):
            await service.connect()
            assert service.is_connected() is True

    @pytest.mark.asyncio
    async def test_redis_service_connect_failure(self):
        """Test Redis connection failure."""
        config = RedisConfig(host="invalid", port=6379)
        service = RedisService(config)

        with patch("app.services.redis_service.aioredis.from_url", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await service.connect()
            assert service.is_connected() is False

    @pytest.mark.asyncio
    async def test_redis_service_disconnect(self):
        """Test Redis disconnection."""
        config = RedisConfig(host="localhost", port=6379)
        service = RedisService(config)

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.aclose = AsyncMock()

        with patch("app.services.redis_service.aioredis.from_url", return_value=mock_client):
            await service.connect()
            await service.disconnect()
            assert service.is_connected() is False
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_service_ping_success(self):
        """Test Redis ping when connected."""
        config = RedisConfig(host="localhost", port=6379)
        service = RedisService(config)

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("app.services.redis_service.aioredis.from_url", return_value=mock_client):
            await service.connect()
            result = await service.ping()
            assert result is True

    @pytest.mark.asyncio
    async def test_redis_service_ping_not_connected(self):
        """Test Redis ping when not connected."""
        config = RedisConfig(host="localhost", port=6379)
        service = RedisService(config)
        result = await service.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_redis_service_ping_failure(self):
        """Test Redis ping failure."""
        config = RedisConfig(host="localhost", port=6379)
        service = RedisService(config)

        mock_client = AsyncMock()
        # First ping succeeds (during connect), second fails (during ping test)
        mock_client.ping = AsyncMock(side_effect=[True, Exception("Ping failed")])

        with patch("app.services.redis_service.aioredis.from_url", return_value=mock_client):
            await service.connect()
            result = await service.ping()
            assert result is False

    @pytest.mark.asyncio
    async def test_redis_service_no_config(self):
        """Test Redis service with no config."""
        with patch("app.services.redis_service.get_redis_config", return_value=None):
            service = RedisService(None)
            await service.connect()  # Should not raise, just log warning
            assert service.is_connected() is False

