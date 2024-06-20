from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4

from box import Box
from litestar import Controller, Request, Response, get, post
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.session.server_side import (
    ServerSideSessionBackend,
    ServerSideSessionConfig,
)
from litestar.openapi.config import OpenAPIConfig
from litestar.security.session_auth import SessionAuth
from litestar.stores.memory import MemoryStore
from pydantic import UUID4, BaseModel, EmailStr, SecretStr

from app.schemas.respone_schema import ResponseWrapper


class UserStatusController(Controller):
    path = "/user"

    @post(path="/login", sync_to_thread=False)
    def loggin(self, data: Box, request: Request):
        if not data.user_id:
            return Response(
                ResponseWrapper(code=2, msg="用户ID不能为空"), status_code=400
            )

        request.session["user_id"] = data.user_id
        return ResponseWrapper(msg="登录成功")

    @get(path="/logout", sync_to_thread=False)
    def logout(self, request: Request):
        request.session.pop("user_id", None)
        return ResponseWrapper()

    @get(path="/id", sync_to_thread=False)
    def retrieve_user(self, request: Request):
        if request.session.get("user_id"):
            return ResponseWrapper({"user_id": request.session["user_id"]})

        return Response(ResponseWrapper(code=1, msg="用户未登录"), status_code=401)
