from box import Box, BoxList
from loguru import logger


def merge_messages_images(messages: list, base64_images: list[str] | None = None):
    if not base64_images:
        logger.debug("No images to merge")
        return messages

    messages = BoxList(messages)

    # 第一条用户消息的内容
    first_user_content = [{"type": "text", "text": messages[1].content}]

    for base64_image in base64_images:
        # 将图片添加到第一条用户消息的内容中
        first_user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            }
        )

    # 更新第一条用户消息的内容
    messages[1].content = first_user_content

    return messages.to_list()


def delete_messages_images(messages: list):
    messages = BoxList(messages)

    for idx, message in enumerate(messages):
        if not isinstance(message.content, list):
            continue

        # 删除图片
        for content in message.content:
            if content.type == "text":
                content_text = content.text

        # 更新消息内容
        messages[idx].content = content_text

    return messages.to_list()
