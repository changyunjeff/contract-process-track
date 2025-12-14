from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class RedisConfig(BaseModel):
    """Redis configuration model."""

    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password (loaded from .env)")
    decode_responses: bool = Field(default=True, description="Decode responses as strings")
    socket_timeout: Optional[int] = Field(default=5, description="Socket timeout in seconds")
    socket_connect_timeout: Optional[int] = Field(default=5, description="Socket connect timeout in seconds")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")

