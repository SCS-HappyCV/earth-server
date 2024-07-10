from base64 import b64encode
from pathlib import Path
import shutil
import socket
import traceback

from fire import Fire
from furl import furl
from loguru import logger
from minio import Minio
from minio.error import S3Error


def get_object_name(name: str, folders: str | list[str]) -> str:
    if isinstance(folders, list):
        folders = Path(*folders)
    elif isinstance(folders, str):
        folders = Path(folders)
    else:
        msg = f"Expected folders to be a str or list[str], got {type(folders)}"
        raise TypeError(msg)

    object_name = folders / name
    object_name = str(object_name)
    return object_name


def get_available_object_name(client: Minio, bucket_name: str, object_name: str) -> str:
    """
    获取可行的 minio 对象名。

    Args:
        client: Minio 客户端实例
        bucket_name: 存储桶名称
        object_name: 初始对象名

    Returns:
        可用的对象名
    """
    try:
        logger.info(f"正在检查对象名: {object_name}")

        # 检查存储桶是否存在
        if not client.bucket_exists(bucket_name):
            logger.error(f"存储桶 {bucket_name} 不存在")
            return object_name

        # 获取对象的路径和扩展名
        object_path = Path(object_name)
        stem = object_path.stem
        suffix = object_path.suffix

        # 检查对象是否存在
        try:
            client.stat_object(bucket_name, object_name)
            logger.info(f"对象 {object_name} 已存在，尝试生成新名称")
        except S3Error as err:
            if err.code == "NoSuchKey":
                logger.info(f"对象 {object_name} 不存在，直接返回")
                return object_name
            else:
                raise  # 如果是其他 S3 错误，则重新抛出

        # 如果对象存在，在对象名后添加数字，直到找到一个不存在的对象名
        counter = 1
        while True:
            name = f"{stem}_{counter}{suffix}"
            object_path = object_path.with_name(name)
            object_name = str(object_path)
            logger.debug(f"尝试新的对象名: {object_name}")

            try:
                client.stat_object(bucket_name, object_name)
                counter += 1
            except S3Error as err:
                if err.code == "NoSuchKey":
                    logger.info(f"找到可用的对象名: {object_name}")
                    return object_name
                else:
                    raise  # 如果是其他 S3 错误，则重新抛出

    except Exception as e:
        logger.error(f"获取可用对象名时发生错误: {e}")
        logger.error(f"错误堆栈跟踪:\n{traceback.format_exc()}")
        return None


def get_object_base64(client: Minio, bucket_name: str, object_name: str) -> str:
    """
    获取 minio 对象的 base64 编码。

    Args:
        client: Minio 客户端实例
        bucket_name: 存储桶名称
        object_name: 对象名

    Returns:
        base64 编码的对象内容
    """
    try:
        logger.info(f"正在获取对象 {object_name} 的 base64 编码")

        # 读取对象内容
        data = client.get_object(bucket_name, object_name)
        data = data.read()

        # 对象内容 base64 编码
        data = b64encode(data).decode("utf-8")
        logger.info(f"获取对象 {object_name} 的 base64 编码成功")

        return data

    except Exception as e:
        logger.error(f"获取对象 {object_name} 的 base64 编码时发生错误: {e}")
        logger.error(f"错误堆栈跟踪:\n{traceback.format_exc()}")
        return None
