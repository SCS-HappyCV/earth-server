from box import Box, BoxList
from loguru import logger
from minio import Minio
from pugsql.compiler import Module

from app.utils.table_funcs import delete_fields

from .object_service import ObjectService


class ProjectService:
    def __init__(self, queries: Module, minio_client: Minio):
        self.queries = queries
        self.object_service = ObjectService(queries, minio_client)

    def create(self, type, name, cover_image_id=None, status="waiting", **kwargs):
        logger.debug(f"Creating project of type {type}")
        if not name:
            name = "未命名项目"

        return self.queries.create_project(
            name=name, type=type, cover_image_id=cover_image_id, status=status
        )

    def get(self, id):
        return self.queries.get_project(id=id)

    def gets(
        self,
        types: tuple[str] = (
            "2d_segmentation",
            "2d_detection",
            "2d_change_detection",
            "3d_segmentation",
        ),
        statuses: tuple[str] = ("waiting", "running", "completed"),
        row_count=9999,
        offset=0,
    ):
        results = self.queries.get_projects(
            row_count=row_count, offset=offset, types=types, statuses=statuses
        )
        results = BoxList(results)

        if results:
            logger.debug(f"Found projects: {results}")
        else:
            logger.debug("No projects found")

        for result in results:
            if not result.cover_image_id:
                continue
            image_info = self.object_service.get_image(id=result.cover_image_id)
            result.cover_image_link = image_info.share_link

        return results

    def update(self, id, name=None, cover_image_id=None):
        if not any([name, cover_image_id]):
            return False

        logger.debug(f"Updating project with id {id}")

        if name:
            self.queries.update_project_name(id=id, name=name)
        if cover_image_id:
            self.queries.update_project_cover_image(
                id=id, cover_image_id=cover_image_id
            )

        return True

    def _populate_project(self, project: dict):
        project = Box(project)

        for key in [
            "cover_image",
            "image",
            "plot_image",
            "image1",
            "image2",
            "mask_svg",
        ]:
            column_name = f"{key}_id"
            if not project.get(column_name):
                continue

            image_info = self.object_service.get_image(id=project[column_name])
            project[f"{key}_link"] = image_info.share_link
            if "thumbnail_link" in image_info:
                project[f"{key}_thumbnail_link"] = image_info.thumbnail_link

        for key in ["pointcloud", "result_pointcloud"]:
            column_name = f"{key}_id"
            if not project.get(column_name):
                continue

            pointcloud_info = self.object_service.get_pointcloud(
                id=project[column_name]
            )
            project[f"{key}_link"] = pointcloud_info.share_link
            # 将key中的pointcloud替换为potree
            key = key.replace("pointcloud", "potree")
            if pointcloud_info.get("potree_link"):
                project[f"{key}_link"] = pointcloud_info.potree_link

        return project

    def delete(self, id):
        return self.queries.delete_project(id=id)
