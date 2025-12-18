"""
工具注册表
用于管理和注册所有可用的工具
"""
from typing import Dict, List, Optional
from threading import Lock
from .tools.base import ToolInterface


class ToolRegistry:
    """
    工具注册表（单例模式）
    
    用于注册、管理和查找工具实例
    """
    _instance: Optional['ToolRegistry'] = None
    _lock: Lock = Lock()

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化注册表"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._tools: Dict[str, ToolInterface] = {}
        self._initialized = True

    def register(self, tool: ToolInterface) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            
        Returns:
            bool: 是否注册成功（如果工具名已存在则返回False）
        """
        if not isinstance(tool, ToolInterface):
            raise TypeError(f"Tool must be an instance of ToolInterface, got {type(tool)}")
        
        if tool.name in self._tools:
            return False
        
        self._tools[tool.name] = tool
        return True

    def register_all(self, tools: List[ToolInterface]) -> Dict[str, bool]:
        """
        批量注册工具
        
        Args:
            tools: 工具实例列表
            
        Returns:
            Dict: 每个工具的注册结果 {tool_name: success}
        """
        results = {}
        for tool in tools:
            results[tool.name] = self.register(tool)
        return results

    def get(self, name: str) -> Optional[ToolInterface]:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            ToolInterface: 工具实例，如果不存在则返回None
        """
        return self._tools.get(name)

    def list_all(self) -> List[ToolInterface]:
        """
        获取所有已注册的工具
        
        Returns:
            List[ToolInterface]: 所有工具实例列表
        """
        return list(self._tools.values())

    def list_names(self) -> List[str]:
        """
        获取所有已注册的工具名称
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())

    def exists(self, name: str) -> bool:
        """
        检查工具是否存在
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 工具是否存在
        """
        return name in self._tools

    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def clear(self):
        """清空所有已注册的工具"""
        self._tools.clear()

    def count(self) -> int:
        """
        获取已注册工具的数量
        
        Returns:
            int: 工具数量
        """
        return len(self._tools)


# 全局单例实例
tool_registry = ToolRegistry()