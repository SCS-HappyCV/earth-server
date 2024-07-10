from box import Box, BoxList
from loguru import logger
from pugsql.compiler import Module

from app.utils.table_funcs import delete_fields


class ProjectService:
    def __init__(self, queries: Module):
        self.queries = queries

    def create(self, type, name, cover_image_id=None, **kwargs):
        logger.debug(f"Creating project of type {type}")
        return self.queries.create_project(
            name=name, type=type, cover_image_id=cover_image_id
        )

    def get(self, id):
        return self.queries.get_project(id=id)

    def list(
        self,
        types: tuple[str] = (
            "2d_segmentation",
            "2d_detection",
            "2d_change_detection",
            "3d_segmentation",
        ),
        row_count=9999,
        offset=0,
    ):
        results = self.queries.get_projects(
            row_count=row_count, offset=offset, types=types
        )
        results = delete_fields(["is_deleted"], rows=results)
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

    def delete(self, id):
        return self.queries.delete_project(id=id)
