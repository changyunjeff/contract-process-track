from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class PostgresConfig(BaseModel):
    """PostgreSQL configuration model."""

    host: str = Field(default="localhost", description="PostgreSQL server host")
    port: int = Field(default=5432, description="PostgreSQL server port")
    database: str = Field(default="process_track", description="PostgreSQL database name")
    user: str = Field(default="postgres", description="PostgreSQL username")
    password: Optional[str] = Field(
        default=None, description="PostgreSQL password (can be loaded from environment)"
    )
    echo: bool = Field(default=False, description="Enable SQLAlchemy echo for debugging")
    pool_size: int = Field(default=5, description="SQLAlchemy connection pool size")
    max_overflow: int = Field(
        default=10, description="SQLAlchemy max overflow connections beyond pool size"
    )


