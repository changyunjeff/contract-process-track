from __future__ import annotations

import time
import logging
from typing import Callable
from fastapi import Request, Response

from starlette.middleware.base import BaseHTTPMiddleware

app_logger = logging.getLogger(__name__)
access_logger = logging.getLogger('access')

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP Request middleware for logging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        client_ip = request.client.host if request.client else "unknown"

        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""

        try:
            response = await call_next(request)

            process_time = time.time() - start_time

            access_logger.info(
                f"📥 Request Start - {method} {path}"
                f"{'?' + query_params if query_params else ''} | "
                f"Client IP: {client_ip}"
            )
            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = time.time() - start_time
            app_logger.error(
                f"❌ Invalid Request - {method} {path} | "
                f"Error: {str(e)} | "
                f"Process Duration: {process_time:.3f}s | "
                f"Client IP: {client_ip}",
                exc_info=True
            )
            raise

