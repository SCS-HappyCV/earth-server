import os

from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", default="localhost")
REDIS_PORT = os.getenv("REDIS_PORT", default="6379")
REDIS_DB = os.getenv("REDIS_DB", default="0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
