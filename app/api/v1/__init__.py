from app.router.register import router_registry, RouterType
from .workflow import workflow_router
from .enterprise import enterprise_router
from .civil_code import civil_code_router

router_registry.add_router(
    router=workflow_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=20,
    name="workflow-v1",
    description="Workflow progress tracking endpoints (v1)",
)

router_registry.add_router(
    router=enterprise_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=30,
    name="enterprise-basic-info-v1",
    description="Enterprise basic info endpoints (v1)",
)

router_registry.add_router(
    router=civil_code_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=40,
    name="civil-code-article-v1",
    description="Civil code article endpoints (v1)",
)

