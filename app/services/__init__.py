from dataclasses import dataclass

from box import Box
from minio import Minio
from pugsql.compiler import Module
from redis import Redis

from .change_detection_2d_service import ChangeDetection2DService
from .conversation_service import ConversationService
from .detection_2d_service import Detection2DService
from .object_service import ObjectService
from .project_service import ProjectService
from .segmentation_2d_service import Segmentation2DService
from .segmentation_3d_service import Segmentation3DService


@dataclass
class Services:
    object_service: ObjectService
    project_service: ProjectService
    conversation_service: ConversationService
    segmentation_2d_service: Segmentation2DService
    segmentation_3d_service: Segmentation3DService
    detection_2d_service: Detection2DService
    change_detection_2d_service: ChangeDetection2DService


def get_services(queries: Module, minio_client: Minio, redis_client: Redis):
    services = {
        "object_service": ObjectService(queries, minio_client),
        "project_service": ProjectService(queries, minio_client),
        "conversation_service": ConversationService(queries, minio_client),
        "segmentation_2d_service": Segmentation2DService(
            queries, minio_client, redis_client
        ),
        "segmentation_3d_service": Segmentation3DService(
            queries, minio_client, redis_client
        ),
        "detection_2d_service": Detection2DService(queries, minio_client, redis_client),
        "change_detection_2d_service": ChangeDetection2DService(
            queries, minio_client, redis_client
        ),
    }

    return Services(**services)


__all__ = (
    "ChangeDetection2DService",
    "Detection2DService",
    "Segmentation2DService",
    "Segmentation3DService",
    "ProjectService",
    "ObjectService",
    "ConversationService",
    "get_services",
)
