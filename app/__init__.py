import json
import mimetypes
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.stores.redis import RedisStore
from minio import Minio
import pugsql
from redis import Redis

from .config import (
    CRSF_SECRET,
    DB_URI,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    QUERIES_PATH,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PORT,
)
from .routes import (
    ConversationController,
    ObjectController,
    ProjectController,
    ProjectTaskController,
)
from .tasks import BackgroudTasksService

load_dotenv(override=True)

cors_config = CORSConfig()
csrf_config = CSRFConfig(CRSF_SECRET)
compression_config = CompressionConfig("brotli")


def retrieve_user_handler(session: dict[str, Any]):
    return {"user_id": user_id} if (user_id := session.get("user_id")) else None


def add_mime_types(app: Litestar):
    # 添加 webp MIME 类型
    mimetypes.add_type("image/webp", ".webp")

    # 添加 avif MIME 类型
    mimetypes.add_type("image/avif", ".avif")

    # 添加 las MIME 类型
    mimetypes.add_type("application/vnd.las", ".las")


backgroud_tasks_service = BackgroudTasksService()
route_handlers = [ObjectController, ProjectTaskController, ConversationController]

app = Litestar(
    route_handlers=route_handlers,
    middleware=[ServerSideSessionConfig().middleware],
    stores={"sessions": RedisStore.with_client()},
    cors_config=cors_config,
    # csrf_config=csrf_config,
    compression_config=compression_config,
    on_startup=[add_mime_types, backgroud_tasks_service.start],
    on_shutdown=[backgroud_tasks_service.stop],
)
