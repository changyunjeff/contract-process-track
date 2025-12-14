from pydantic import BaseModel, Field
from typing import Optional

class AppConfig(BaseModel):
    title: Optional[str] = Field(default=None, description="Title of the application")
    host: str = Field(..., description="Host of the application")
    port: int = Field(default=8516, description="Port of the application")
    version: Optional[str] = Field(default=None, description="Version of the application")