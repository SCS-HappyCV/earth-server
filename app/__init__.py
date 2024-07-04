from pathlib import Path
from typing import Any

from litestar import Litestar
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.stores.redis import RedisStore
from minio import Minio
import pugsql

from .config import (
    CRSF_SECRET,
    DB_URI,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    QUERIES_PATH,
)
from .routes import ObjectController, ProjectController, ProjectTaskController

cors_config = CORSConfig()
csrf_config = CSRFConfig(CRSF_SECRET)
compression_config = CompressionConfig("brotli")


def retrieve_user_handler(session: dict[str, Any]):
    return {"user_id": user_id} if (user_id := session.get("user_id")) else None


def get_db_connection(app: Litestar):
    queries_path = Path(QUERIES_PATH).expanduser().resolve()
    queries = pugsql.module(queries_path)
    queries.connect(DB_URI)

    minio_clent = Minio(
        MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False
    )

    app.state.queries = queries
    app.state.minio_client = minio_clent


def close_db_connection(app: Litestar):
    queries: pugsql.compiler.Module = app.state.queries
    queries.disconnect()


route_handlers = [ObjectController, ProjectController, ProjectTaskController]

app = Litestar(
    route_handlers=route_handlers,
    middleware=[ServerSideSessionConfig().middleware],
    stores={"sessions": RedisStore.with_client()},
    cors_config=cors_config,
    # csrf_config=csrf_config,
    compression_config=compression_config,
    on_startup=[get_db_connection],
    on_shutdown=[close_db_connection],
)
