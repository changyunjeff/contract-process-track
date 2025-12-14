from __future__ import annotations

from typing import Optional
from pydantic import BaseModel
from .app_config import AppConfig
from .redis_config import RedisConfig

class GlobalConfig(BaseModel):
    app: AppConfig
    redis: Optional[RedisConfig] = None

__all__=["GlobalConfig", "AppConfig", "RedisConfig"]