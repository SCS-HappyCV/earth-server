import json
import mimetypes
from pathlib import Path
import threading
from typing import Any

from box import Box
from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.stores.redis import RedisStore
from loguru import logger
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
from .tasks import background_tasks

cors_config = CORSConfig()
csrf_config = CSRFConfig(CRSF_SECRET)
compression_config = CompressionConfig("brotli")

stop_event = threading.Event()


def retrieve_user_handler(session: dict[str, Any]):
    return {"user_id": user_id} if (user_id := session.get("user_id")) else None


def get_db_connection(app: Litestar):
    queries_path = Path(QUERIES_PATH).expanduser().resolve()
    queries = pugsql.module(queries_path)
    queries.connect(DB_URI)

    minio_clent = Minio(
        MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False
    )
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    app.state.queries = queries
    app.state.minio_client = minio_clent
    app.state.redis_client = redis_client


def close_db_connection(app: Litestar):
    queries: pugsql.compiler.Module = app.state.queries
    queries.disconnect()

    redis_client: Redis = app.state.redis_client
    redis_client.close()


def add_mime_types(app: Litestar):
    # 添加 webp MIME 类型
    mimetypes.add_type("image/webp", ".webp")

    # 添加 avif MIME 类型
    mimetypes.add_type("image/avif", ".avif")


def start_tasks(app: Litestar):
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    queris = pugsql.module(QUERIES_PATH)
    queris.connect(DB_URI)

    minio_client = Minio(
        MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False
    )

    kwargs = {
        "stop_event": stop_event,
        "redis_client": redis_client,
        "queries": queris,
        "minio_client": minio_client,
    }
    threading.Thread(target=background_tasks, kwargs=kwargs).start()


route_handlers = [
    ObjectController,
    ProjectController,
    ProjectTaskController,
    ConversationController,
]

app = Litestar(
    route_handlers=route_handlers,
    middleware=[ServerSideSessionConfig().middleware],
    stores={"sessions": RedisStore.with_client()},
    cors_config=cors_config,
    # csrf_config=csrf_config,
    compression_config=compression_config,
    on_startup=[get_db_connection, add_mime_types, start_tasks],
    on_shutdown=[close_db_connection],
)
