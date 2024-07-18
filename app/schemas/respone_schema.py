from typing import Any

from pydantic.dataclasses import dataclass


@dataclass
class ResponseWrapper:
    """响应数据"""

    """数据"""
    data: Any = None

    """错误码"""
    code: int = 0

    """错误消息"""
    message: str = ""


@dataclass
class Pagination:
    """分页信息"""

    """总数"""
    total: int = 0

    """起始位置"""
    start: int = 0

    """长度"""
    length: int = 0

    """数据"""
    data: Any = None
