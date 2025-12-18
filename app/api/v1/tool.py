"""
工具API路由（v1版本）

提供工具相关的HTTP API端点，支持Langdock Integration调用
"""
from __future__ import annotations

from fastapi import APIRouter

from app.models import HttpResponse
from app.exceptions import BadRequestException, InternalServerException, NotFoundException
from app.tool.registry import tool_registry
from app.tool.dto import (
    ToolInfoDTO,
    ToolListResponseDTO,
    ToolExecuteRequestDTO,
    ToolExecuteResponseDTO,
    ToolListOpenAIResponseDTO,
)

tool_router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@tool_router.get("/", response_model=HttpResponse[ToolListResponseDTO])
async def list_tools() -> HttpResponse[ToolListResponseDTO]:
    """
    获取所有可用工具列表
    
    返回所有已注册的工具及其基本信息
    """
    try:
        tools = tool_registry.list_all()
        tool_infos = [
            ToolInfoDTO(
                name=tool.name,
                description=tool.description,
                parameters_schema=tool.get_parameters_schema()
            )
            for tool in tools
        ]
        
        response_data = ToolListResponseDTO(
            tools=tool_infos,
            count=len(tool_infos)
        )
        
        return HttpResponse.success(
            data=response_data,
            msg="获取工具列表成功"
        )
    except Exception as e:
        raise InternalServerException(f"获取工具列表失败: {str(e)}")


@tool_router.get("/openai", response_model=HttpResponse[ToolListOpenAIResponseDTO])
async def list_tools_openai() -> HttpResponse[ToolListOpenAIResponseDTO]:
    """
    获取所有可用工具列表（OpenAI格式，兼容Langdock）
    
    返回OpenAI Function Calling格式的工具定义，可直接用于Langdock Integration
    """
    try:
        tools = tool_registry.list_all()
        openai_tools = [tool.to_openai_schema() for tool in tools]
        
        response_data = ToolListOpenAIResponseDTO(
            tools=openai_tools,
            count=len(openai_tools)
        )
        
        return HttpResponse.success(
            data=response_data,
            msg="获取工具列表成功（OpenAI格式）"
        )
    except Exception as e:
        raise InternalServerException(f"获取工具列表失败: {str(e)}")


@tool_router.get("/{tool_name}", response_model=HttpResponse[ToolInfoDTO])
async def get_tool_info(tool_name: str) -> HttpResponse[ToolInfoDTO]:
    """
    获取指定工具的详细信息
    
    Args:
        tool_name: 工具名称
    """
    try:
        tool = tool_registry.get(tool_name)
        if tool is None:
            raise NotFoundException(f"工具不存在: {tool_name}")
        
        tool_info = ToolInfoDTO(
            name=tool.name,
            description=tool.description,
            parameters_schema=tool.get_parameters_schema()
        )
        
        return HttpResponse.success(
            data=tool_info,
            msg="获取工具信息成功"
        )
    except NotFoundException:
        raise
    except Exception as e:
        raise InternalServerException(f"获取工具信息失败: {str(e)}")


@tool_router.get("/{tool_name}/openai", response_model=HttpResponse[dict])
async def get_tool_openai_schema(tool_name: str) -> HttpResponse[dict]:
    """
    获取指定工具的OpenAI格式定义（兼容Langdock）
    
    Args:
        tool_name: 工具名称
    """
    try:
        tool = tool_registry.get(tool_name)
        if tool is None:
            raise NotFoundException(f"工具不存在: {tool_name}")
        
        openai_schema = tool.to_openai_schema()
        
        return HttpResponse.success(
            data=openai_schema,
            msg="获取工具OpenAI格式定义成功"
        )
    except NotFoundException:
        raise
    except Exception as e:
        raise InternalServerException(f"获取工具OpenAI格式定义失败: {str(e)}")


@tool_router.post("/execute", response_model=HttpResponse[ToolExecuteResponseDTO])
async def execute_tool(request: ToolExecuteRequestDTO) -> HttpResponse[ToolExecuteResponseDTO]:
    """
    执行工具
    
    根据提供的工具名称和输入参数执行工具，返回执行结果。
    支持Langdock Integration调用。
    
    Args:
        request: 工具执行请求，包含工具名称、输入参数和执行上下文
    """
    try:
        # 验证工具是否存在
        tool = tool_registry.get(request.tool_name)
        if tool is None:
            raise NotFoundException(f"工具不存在: {request.tool_name}")
        
        # 执行工具
        try:
            result = tool.run(request.input, request.context or {})
            success = result.get("type") != "error"
            
            response_data = ToolExecuteResponseDTO(
                tool_name=request.tool_name,
                result=result,
                success=success
            )
            
            return HttpResponse.success(
                data=response_data,
                msg="工具执行成功" if success else "工具执行完成（有错误）"
            )
        except ValueError as e:
            raise BadRequestException(f"工具执行参数错误: {str(e)}")
        except Exception as e:
            # 工具执行异常，返回错误结果
            error_result = {
                "type": "error",
                "error": str(e),
                "tool_name": request.tool_name
            }
            response_data = ToolExecuteResponseDTO(
                tool_name=request.tool_name,
                result=error_result,
                success=False
            )
            return HttpResponse.success(
                data=response_data,
                msg=f"工具执行失败: {str(e)}"
            )
            
    except NotFoundException:
        raise
    except BadRequestException:
        raise
    except Exception as e:
        raise InternalServerException(f"执行工具失败: {str(e)}")


@tool_router.post("/{tool_name}/execute", response_model=HttpResponse[ToolExecuteResponseDTO])
async def execute_tool_by_name(
    tool_name: str,
    input: dict,
    context: dict = None
) -> HttpResponse[ToolExecuteResponseDTO]:
    """
    通过工具名称执行工具（简化版接口）
    
    这是一个便捷接口，可以直接通过URL路径指定工具名称，请求体只需要包含输入参数。
    
    Args:
        tool_name: 工具名称（URL路径参数）
        input: 工具输入参数（请求体）
        context: 执行上下文（可选，请求体）
    """
    try:
        # 验证工具是否存在
        tool = tool_registry.get(tool_name)
        if tool is None:
            raise NotFoundException(f"工具不存在: {tool_name}")
        
        # 执行工具
        try:
            result = tool.run(input, context or {})
            success = result.get("type") != "error"
            
            response_data = ToolExecuteResponseDTO(
                tool_name=tool_name,
                result=result,
                success=success
            )
            
            return HttpResponse.success(
                data=response_data,
                msg="工具执行成功" if success else "工具执行完成（有错误）"
            )
        except ValueError as e:
            raise BadRequestException(f"工具执行参数错误: {str(e)}")
        except Exception as e:
            # 工具执行异常，返回错误结果
            error_result = {
                "type": "error",
                "error": str(e),
                "tool_name": tool_name
            }
            response_data = ToolExecuteResponseDTO(
                tool_name=tool_name,
                result=error_result,
                success=False
            )
            return HttpResponse.success(
                data=response_data,
                msg=f"工具执行失败: {str(e)}"
            )
            
    except NotFoundException:
        raise
    except BadRequestException:
        raise
    except Exception as e:
        raise InternalServerException(f"执行工具失败: {str(e)}")

