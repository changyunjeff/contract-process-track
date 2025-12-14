from pydantic import BaseModel
from .app_config import AppConfig

class GlobalConfig(BaseModel):
    app: AppConfig

__all__=["GlobalConfig", "AppConfig"]