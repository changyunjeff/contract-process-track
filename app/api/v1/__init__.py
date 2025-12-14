from app.router.register import router_registry, RouterType
from .workflow import workflow_router

router_registry.add_router(
    router=workflow_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=20,
    name="workflow-v1",
    description="Workflow progress tracking endpoints (v1)"
)

