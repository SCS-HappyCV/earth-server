from dataclasses import dataclass

from minio import Minio
import pugsql
from redis import Redis

from app.config import (
    DB_URI,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    QUERIES_PATH,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PORT,
)


@dataclass
class ConnectionsManager:
    db_uri: str = DB_URI
    minio_endpoint: str = MINIO_ENDPOINT
    minio_access_key: str = MINIO_ACCESS_KEY
    minio_secret_key: str = MINIO_SECRET_KEY
    redis_host: str = REDIS_HOST
    redis_port: int = REDIS_PORT
    redis_db: int = REDIS_DB
    queries_path: str = QUERIES_PATH

    def open(self):
        self.queries = pugsql.module(self.queries_path)
        self.queries.connect(self.db_uri)

        self.minio_client = Minio(
            self.minio_endpoint,
            self.minio_access_key,
            self.minio_secret_key,
            secure=False,
        )

        self.redis_client = Redis(self.redis_host, self.redis_port, self.redis_db)

    def close(self):
        self.queries.disconnect()
        self.redis_client.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return True
