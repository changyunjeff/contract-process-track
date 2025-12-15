from __future__ import annotations

from typing import Optional
from pydantic import BaseModel
from .app_config import AppConfig
from .redis_config import RedisConfig
from .postgres_config import PostgresConfig


class GlobalConfig(BaseModel):
    app: AppConfig
    redis: Optional[RedisConfig] = None
    postgres: Optional[PostgresConfig] = None


__all__ = ["GlobalConfig", "AppConfig", "RedisConfig", "PostgresConfig"]