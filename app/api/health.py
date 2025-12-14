from __future__ import annotations

from fastapi import APIRouter
from app.models import HttpResponse

health_router = APIRouter(prefix="/api", tags=["health"])

@health_router.get("/health")
async def health() -> HttpResponse:
    return HttpResponse.success()

@health_router.get("/fail")
async def fail() -> HttpResponse:
    return HttpResponse.error(msg="fail", data={"err":"fail"})
