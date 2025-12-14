from app.router.register import router_registry, RouterType
from .health import health_router

router_registry.add_router(
    router=health_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=10,
    name="health",
    description="Health check endpoint"
)
