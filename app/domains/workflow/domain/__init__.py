"""领域层：包含实体、值对象和仓储接口"""

from .entities import WorkflowProgress
from .repositories import IWorkflowProgressRepository

__all__ = ["WorkflowProgress", "IWorkflowProgressRepository"]

