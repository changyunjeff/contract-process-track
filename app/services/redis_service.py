from __future__ import annotations

import logging
import os
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.config import get_redis_config
from app.configs import RedisConfig

logger = logging.getLogger(__name__)

_redis_client: Optional[Redis] = None


class RedisService:
    """Redis connection service."""

    def __init__(self, config: Optional[RedisConfig] = None):
        """
        Initialize Redis service.

        Args:
            config: Redis configuration. If None, will load from global config.
        """
        self.config = config or get_redis_config()
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis server."""
        if self.config is None:
            logger.warning("Redis configuration not found, skipping Redis connection")
            return

        try:
            # Get password from environment variable if not in config
            password = self.config.password
            if password is None:
                password = os.getenv("REDIS_PASSWORD")

            self._client = aioredis.from_url(
                f"redis://{self.config.host}:{self.config.port}/{self.config.db}",
                password=password,
                decode_responses=self.config.decode_responses,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
            )

            # Test connection
            await self._client.ping()
            logger.info(
                f"✅ Redis connected successfully to {self.config.host}:{self.config.port}/{self.config.db}"
            )

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Failed to connect to Redis: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Redis: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Redis server."""
        if self._client:
            try:
                await self._client.aclose()
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.error(f"❌ Error closing Redis connection: {str(e)}")
            finally:
                self._client = None

    async def ping(self) -> bool:
        """Check if Redis connection is alive."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    @property
    def client(self) -> Optional[Redis]:
        """Get Redis client instance."""
        return self._client

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._client is not None


# Global Redis service instance
_redis_service: Optional[RedisService] = None


async def init_redis_service(config: Optional[RedisConfig] = None) -> RedisService:
    """
    Initialize global Redis service.

    Args:
        config: Redis configuration. If None, will load from global config.

    Returns:
        RedisService instance
    """
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService(config)
        await _redis_service.connect()
    return _redis_service


async def close_redis_service() -> None:
    """Close global Redis service connection."""
    global _redis_service
    if _redis_service:
        await _redis_service.disconnect()
        _redis_service = None


def get_redis_service() -> Optional[RedisService]:
    """Get global Redis service instance."""
    return _redis_service

