import json

from box import Box
from redis import Redis

from app.config import TASK_QUEUE


def push_task(
    redis_client: Redis,
    task: dict | None = None,
    tasks: list[dict] | None = None,
    task_queue: str = TASK_QUEUE,
):
    if task:
        tasks = [task]

    for task_info in tasks:
        redis_client.rpush(
            task_queue,
            json.dumps(task_info, ensure_ascii=False, indent="\t", default=str),
        )


def get_task(redis_client: Redis, task_queue: str = TASK_QUEUE) -> Box:
    _, task_info = redis_client.blpop(task_queue)
    task_info = task_info.decode("utf-8")
    task_info = Box().from_json(task_info)

    return task_info
