import json

from redis import Redis

from app.config import TASK_QUEUE


def push_task(
    redis_client: Redis, task: dict | None = None, tasks: list[dict] | None = None
):
    if task:
        tasks = [task]

    for task_info in tasks:
        redis_client.rpush(
            TASK_QUEUE,
            json.dumps(task_info, ensure_ascii=False, indent="\t", default=str),
        )
