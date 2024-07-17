import json

from box import Box, BoxList
from loguru import logger
from pugsql.compiler import Module

from app.utils.conversation_funcs import delete_messages_images, merge_messages_images

from .object_service import ObjectService
from .project_service import ProjectService


class ConversationService:
    def __init__(self, queries: Module, minio_client):
        self.queries = queries
        self.project_service = ProjectService(queries, minio_client)
        self.object_service = ObjectService(queries, minio_client)

    def create(self, name, image_ids: list, messages: list, **kwargs):
        with self.queries.transaction() as tx:
            cover_image_id = image_ids[0] if image_ids else None
            # 创建project
            project_id = self.project_service.create(
                name=name,
                type="conversation",
                cover_image_id=cover_image_id,
                status="completed",
            )

            if not project_id:
                tx.rollback()

                msg = "Failed to create project"
                raise ValueError(msg)

            # 创建conversation
            messages = delete_messages_images(messages)

            conversation_id = self.queries.create_conversation(
                messages=json.dumps(messages, ensure_ascii=False), project_id=project_id
            )

            if not conversation_id:
                tx.rollback()

                msg = "Failed to create conversation"
                raise ValueError(msg)

            # 创建conversation_images
            for image_id in image_ids:
                conversation_image_id = self.queries.create_conversation_image(
                    conversation_id=conversation_id, image_id=image_id
                )

                if not conversation_image_id:
                    tx.rollback()

                    msg = "Failed to create conversation image"
                    raise ValueError(msg)

        conversation = {"id": conversation_id, "image_ids": image_ids}

        return conversation

    def get(self, *, id=None, project_id=None):
        if id:
            conversation = self.queries.get_conversation(id=id)
        elif project_id:
            conversation = self.queries.get_conversation_by_project_id(project_id)
        else:
            logger.error(f"ID{id} or project_id must be provided")
            return None

        if not conversation:
            logger.error(f"Conversation {id} not found")
            return None

        conversation = Box(conversation)

        # 获取对话中的所有图片id
        image_ids = self.queries.get_conversation_image_ids(
            conversation_id=conversation.id
        )
        image_ids = [image_id.image_id for image_id in BoxList(image_ids)]
        # 获取所有图片
        images = self.object_service.get_images(
            ids=image_ids, should_base64=True, only_thumbnail=True
        )

        logger.debug(f"images: {[image.keys() for image in images]}")

        # 获取所有图片的 base64 编码
        base64_images = [
            image.get("base64_thumbnail") or image.get("base64_image")
            for image in images
        ]
        # 合并消息和图片
        messages = merge_messages_images(
            json.loads(conversation.messages), base64_images
        )

        # 删除 base64_ 开头的属性
        for image in images:
            for key in list(image.keys()):
                if key.startswith("base64_"):
                    del image[key]

        # 删除 conversation 中的 messages 属性
        del conversation["messages"]
        # 合并所有信息
        conversation_info = {**conversation, "messages": messages, "images": images}

        return conversation_info

    def gets(self):
        conversations = self.queries.get_conversations()
        conversations = BoxList(conversations)

        for conversation in conversations:
            cover_image = self.object_service.get_image(conversation.cover_image_id)
            conversation.cover_image = cover_image

        return conversations

    def update(self, id, messages: list, **kwargs):
        # 更新conversation
        messages = delete_messages_images(messages)

        conversation = self.queries.update_conversation(
            id=id, messages=json.dumps(messages, ensure_ascii=False)
        )

        if not conversation:
            msg = "Failed to update conversation"
            raise ValueError(msg)

        return conversation

    def delete(self, id=None, project_id=None):
        if id or project_id:
            return self.queries.delete_2d_detection(id=id, project_id=project_id)
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)
