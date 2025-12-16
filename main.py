from __future__ import annotations

import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from typing_extensions import AsyncIterator
from app.middleware.logging import LoggingMiddleware
from dotenv import load_dotenv

from app.my_logging import setup_logging
from app.configs import AppConfig
from app.config import get_app_config
from app.router import setup_routers
from app.services.redis_service import init_redis_service, close_redis_service
from app.services.postgres_service import init_postgres_service, close_postgres_service


# Load .env file from project root if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # =====================[ Start Up ]======================
    logger.info("🚀 Application starting up...")
    
    # Initialize Redis connection
    try:
        await init_redis_service()
    except Exception as e:
        logger.warning(f"⚠️ Redis initialization failed: {str(e)}. Continuing without Redis.")

    # Initialize PostgreSQL connections for all configured databases
    try:
        init_postgres_service()  # 初始化所有配置的数据库
    except Exception as e:
        logger.warning(
            f"⚠️ PostgreSQL initialization failed: {str(e)}. "
            f"Continuing without PostgreSQL."
        )
    
    yield
    # =====================[ Shut Down ]======================
    logger.info("🛑 Application shutting down...")
    
    # Close Redis connection
    try:
        await close_redis_service()
    except Exception as e:
        logger.warning(f"⚠️ Redis shutdown error: {str(e)}")

    # Dispose all PostgreSQL engines
    try:
        await close_postgres_service()  # 关闭所有数据库连接
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL shutdown error: {str(e)}")


def create_app(app_config: AppConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    if app_config is None:
        app_config = get_app_config()

    # 标记这是真正的应用启动（不是reloader进程的预检查）
    # 在reload模式下，reloader进程会先导入模块检查代码，但不会调用create_app
    # 只有当真正启动server时，才会调用create_app
    # 所以我们在这里设置环境变量，标记这是server进程
    os.environ["PROCESS_TRACK_SERVER"] = "true"

    setup_logging(is_debug_mode(os.getenv("MODE", "dev")))

    # Check if favicon exists
    favicon_path = Path("static/favicon.ico")
    favicon_url = "/static/favicon.ico" if favicon_path.exists() else None

    _app = FastAPI(
        title=app_config.title or "Process Track",
        version=app_config.version or "0.1.0",
        lifespan=lifespan,
        swagger_ui_parameters={
            "faviconUrl": favicon_url or "/favicon.ico"
        } if favicon_url else None,
    )
    _app.add_middleware(LoggingMiddleware)

    # mount static files
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
    _app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Add favicon route
    @_app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Serve favicon.ico"""
        favicon_file = Path("static/favicon.ico")
        if favicon_file.exists():
            return FileResponse(favicon_file)
        # Return 204 No Content if favicon doesn't exist
        return Response(status_code=204)

    # register routers
    try:
        status = setup_routers(_app)
    except Exception as e:
        raise
    
    return _app


def is_debug_mode(_mode: str) -> bool:
    """Check if the application is running in debug mode."""
    debug_modes = {"dev", "development", "debug"}
    return _mode.lower() in debug_modes


def worker_count() -> int:
    return  1 # os.cpu_count()


# Create an app instance at module level for uvicorn reload support
cfg = get_app_config()
app = create_app(cfg)

if __name__ == "__main__":
    mode = os.getenv("MODE", "dev").lower()
    debug = is_debug_mode(mode)
    
    uvicorn_config = {
        "host": cfg.host,
        "port": cfg.port,
        # "reload": debug,
        # "workers": worker_count() if not debug else 1,
        "log_config": None,
    }
    
    # Always pass as import string when using reload or workers>1
    # This avoids uvicorn's warning and supports both dev (reload) and prod (workers>1)

    if debug:
        uvicorn_config["app"] = "main:app"
    else:
        uvicorn_config["app"] = app

    uvicorn.run(**uvicorn_config)
