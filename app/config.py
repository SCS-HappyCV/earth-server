import os

from dotenv import load_dotenv

load_dotenv(override=True)

QUERIES_PATH = "app/queries/"

DATABASE_NAME = os.getenv("DATABASE_NAME", default="ai_earth")
DATABASE_USER = os.getenv("DATABASE_USER", default="super")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST", default="localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", default="3306")

REDIS_HOST = os.getenv("REDIS_HOST", default="localhost")
REDIS_PORT = os.getenv("REDIS_PORT", default="6379")
REDIS_DB = os.getenv("REDIS_DB", default="0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

DB_URI = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", default="localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", default="minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", default="minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", default="ai-earth")


CRSF_SECRET = os.getenv("CSRF_SECRET")

# 公网访问地址
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", default="http://localhost")

SHARE_LINK_BASE_URL = os.getenv(
    "SHARE_LINK_BASE_URL", default=f"{PUBLIC_BASE_URL}/file"
)
POTREE_BASE_URL = os.getenv("POTREE_BASE_URL", default=f"{PUBLIC_BASE_URL}/potree")
POTREE_SERVER_ROOT = os.getenv("POTREE_SERVER_ROOT", default="/srv/www/potree")
POTREE_CLOUD_FOLDER = os.getenv("POTREE_CLOUD_FOLDER", default="pointclouds")
POTREE_VIEWER_FOLDER = os.getenv("POTREE_VIEWER_FOLDER", default="viewer")

TMPDIR = os.getenv("TMPDIR", default="/tmp")

# 任务队列
TASK_QUEUE = os.getenv("TASK_QUEUE", default="tasks")
