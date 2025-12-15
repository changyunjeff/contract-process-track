"""领域层：包含实体和值对象以及仓储接口"""

from .entities import EnterpriseBasicInfo
from .repositories import IEnterpriseBasicInfoRepository

__all__ = ["EnterpriseBasicInfo", "IEnterpriseBasicInfoRepository"]



