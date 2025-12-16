from pydantic import BaseModel, model_serializer
from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')

ERROR_CODE = 7

class HttpResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    code: int = 0  # 0 表示成功，非 0 表示业务错误
    msg: str = "ok"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, msg: str = "ok"):
        return cls(code=0, msg=msg, data=data)

    @classmethod
    def error(cls, msg: str, data: T = None):
        return cls(code=ERROR_CODE, msg=msg, data=data)

    @classmethod
    def notfound(cls, msg: str = "Not Found"):
        return cls(code=404, msg=msg)

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """
        序列化时过滤空值：
        - 过滤 None 的 data
        - 过滤空字符串的 msg
        """
        result = {"code": self.code}
        
        # 只有当 msg 不为空字符串时才包含
        if self.msg:
            result["msg"] = self.msg
        
        # 只有当 data 不为 None 时才包含
        if self.data is not None:
            result["data"] = self.data
        
        return result

