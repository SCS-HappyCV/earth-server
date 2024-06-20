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
