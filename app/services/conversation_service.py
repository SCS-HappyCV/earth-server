import json

from box import Box, BoxList
from pugsql.compiler import Module

from app.utils.conversation_funcs import delete_messages_images, merge_messages_images

from .object_service import ObjectService
from .project_service import ProjectService


class ConversationService:
    def __init__(self, queries: Module, minio_client):
        self.queries = queries
        self.project_service = ProjectService(queries)
        self.object_service = ObjectService(queries, minio_client)
        self.project_service = ProjectService(queries)

    def create(self, name, image_ids: list, messages: list, **kwargs):
        with self.queries.transaction() as tx:
            # 创建project
            project_id = self.project_service.create(
                name=name, type="conversation", cover_image_id=image_ids[0]
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
            msg = "ID or project_id must be provided"
            raise ValueError(msg)

        # 获取对话中的所有消息
        conversation = BoxList(conversation)

        # 获取对话中的所有图片
        images = BoxList()
        for conv in conversation:
            image_id = conv.image_id
            image = self.object_service.get_image(image_id, should_base64=True)
            if not image:
                msg = "Failed to get image"
                raise ValueError(msg)

            images.append(image)

        # 获取所有图片的 base64 编码
        base64_images = [image.base64_image for image in images]
        messages = merge_messages_images(
            json.loads(conversation[0].messages), base64_images
        )

        # 删除 base64_image 属性
        for image in images:
            image.pop("base64_image")

        # 返回对话中的所有消息和图片
        conversation = {"id": id, "messages": messages, "images": images}

        return conversation

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
        if id:
            return self.queries.delete_2d_detection(id=id)
        elif project_id:
            return self.queries.delete_2d_detections_by_project_id(
                project_id=project_id
            )
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)
