"""
Integration tests for Redis service.

These tests require a running Redis instance.
Use pytest markers to skip if Redis is not available:
    pytest -m "not integration"  # Skip integration tests
    pytest -m integration         # Run only integration tests
"""
import os
import pytest
import pytest_asyncio
from app.services.redis_service import RedisService, init_redis_service, close_redis_service, get_redis_service
from app.configs.redis_config import RedisConfig


@pytest.fixture
def redis_config():
    """Fixture for Redis configuration."""
    return RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )


@pytest_asyncio.fixture
async def redis_service(redis_config):
    """Fixture for Redis service."""
    service = RedisService(redis_config)
    try:
        await service.connect()
        yield service
    finally:
        await service.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisIntegration:
    """Integration tests for Redis service."""

    async def test_redis_connection(self, redis_service):
        """Test basic Redis connection."""
        assert redis_service.is_connected() is True
        ping_result = await redis_service.ping()
        assert ping_result is True

    async def test_redis_set_get(self, redis_service):
        """Test Redis set and get operations."""
        if not redis_service.is_connected():
            pytest.skip("Redis not connected")

        client = redis_service.client
        assert client is not None

        # Test set and get
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        assert value == "test_value"

        # Cleanup
        await client.delete("test_key")

    async def test_redis_set_get_with_ttl(self, redis_service):
        """Test Redis set with TTL and get operations."""
        if not redis_service.is_connected():
            pytest.skip("Redis not connected")

        client = redis_service.client
        assert client is not None

        # Test set with TTL
        await client.set("test_key_ttl", "test_value_ttl", ex=10)
        value = await client.get("test_key_ttl")
        assert value == "test_value_ttl"

        # Check TTL
        ttl = await client.ttl("test_key_ttl")
        assert 0 < ttl <= 10

        # Cleanup
        await client.delete("test_key_ttl")

    async def test_redis_delete(self, redis_service):
        """Test Redis delete operation."""
        if not redis_service.is_connected():
            pytest.skip("Redis not connected")

        client = redis_service.client
        assert client is not None

        # Set a key
        await client.set("test_delete_key", "test_value")
        value = await client.get("test_delete_key")
        assert value == "test_value"

        # Delete the key
        result = await client.delete("test_delete_key")
        assert result == 1

        # Verify deletion
        value = await client.get("test_delete_key")
        assert value is None

    async def test_redis_exists(self, redis_service):
        """Test Redis exists operation."""
        if not redis_service.is_connected():
            pytest.skip("Redis not connected")

        client = redis_service.client
        assert client is not None

        # Key doesn't exist
        exists = await client.exists("test_exists_key")
        assert exists == 0

        # Set key
        await client.set("test_exists_key", "test_value")
        exists = await client.exists("test_exists_key")
        assert exists == 1

        # Cleanup
        await client.delete("test_exists_key")

    async def test_redis_hash_operations(self, redis_service):
        """Test Redis hash operations."""
        if not redis_service.is_connected():
            pytest.skip("Redis not connected")

        client = redis_service.client
        assert client is not None

        # Set hash fields
        await client.hset("test_hash", mapping={"field1": "value1", "field2": "value2"})

        # Get hash field
        value = await client.hget("test_hash", "field1")
        assert value == "value1"

        # Get all hash fields
        all_fields = await client.hgetall("test_hash")
        assert all_fields == {"field1": "value1", "field2": "value2"}

        # Cleanup
        await client.delete("test_hash")

    async def test_global_redis_service(self, redis_config):
        """Test global Redis service initialization."""
        # Clean up any existing service
        await close_redis_service()

        # Initialize service
        service = await init_redis_service(redis_config)
        assert service is not None
        assert service.is_connected() is True

        # Get service
        retrieved_service = get_redis_service()
        assert retrieved_service == service

        # Cleanup
        await close_redis_service()
        assert get_redis_service() is None

    async def test_redis_service_reconnect(self, redis_config):
        """Test Redis service reconnection."""
        service = RedisService(redis_config)
        await service.connect()
        assert service.is_connected() is True

        await service.disconnect()
        assert service.is_connected() is False

        await service.connect()
        assert service.is_connected() is True

        await service.disconnect()

