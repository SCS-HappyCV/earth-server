import traceback

from furl import furl
from loguru import logger


def rewrite_base_url(url: str, base_url: str) -> str:
    """
    重写给定URL的base_url。

    :param url: 原始URL
    :param base_url: 新的base URL
    :return: 重写后的URL

    >>> rewrite_url("https://localhost:9001/a.png", "http://zw403-1080ti/file")
    'http://zw403-1080ti/file/a.png'
    """
    logger.info(f"开始重写URL。原始URL: {url}, 新的base URL: {base_url}")

    try:
        # 解析原始URL和新的base URL
        url: furl = furl(url)
        base_url: furl = furl(base_url)

        # 重写URL
        url.origin = base_url.origin
        url.port = base_url.port
        url.path.segments = [*base_url.path.segments, *url.path.segments]

        logger.info(f"URL重写成功。重写后的URL: {url}")
        return str(url)

    except Exception as e:
        err_msg = f"重写URL时发生错误: {e}"
        logger.error(f"{err_msg}\n{traceback.format_exc()}")
        raise
