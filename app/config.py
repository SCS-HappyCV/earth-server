import os

from dotenv import load_dotenv

load_dotenv()

QUERIES_PATH = "app/queries/"

DATABASE_NAME = os.getenv("DATABASE_NAME", default="ai_earth")
DATABASE_USER = os.getenv("DATABASE_USER", default="super")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST", default="localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", default="3306")

DB_URI = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", default="localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", default="minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", default="minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", default="ai-earth")

CRSF_SECRET = os.getenv("CSRF_SECRET")
