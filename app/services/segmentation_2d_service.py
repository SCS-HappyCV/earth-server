from box import Box, BoxList
from pugsql.compiler import Module

from app.utils.table_funcs import delete_fields

from .project_service import ProjectService


class Segmentation2DService:
    def __init__(self, queries: Module):
        self.queries = queries
        self.project_service = ProjectService(queries)

    def create(self, image_id, project_id=None, project_name=None, **kwargs):
        with self.queries.transaction() as tx:
            if project_id:
                project = self.project_service.get(project_id)
                if not project:
                    tx.rollback()

                    msg = f"Project with id {project_id} does not exist"
                    raise ValueError(msg)
            else:
                project_id = self.project_service.create(
                    type="2d_detection", name=project_name, cover_image_id=image_id
                )

            last_id = self.queries.create_2d_detection(
                project_id=project_id, image_id=image_id
            )
            if not last_id:
                tx.rollback()

                msg = "Failed to create 2d detection"
                raise ValueError(msg)

        return last_id, project_id

    def get(self, *, id=None, project_id=None):
        if id:
            return self.queries.get_2d_detection(id=id)
        elif project_id:
            return self.queries.get_2d_segmentation_by_project_id(project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def delete(self, id=None, project_id=None):
        if id:
            return self.queries.delete_2d_detection(id=id)
        elif project_id:
            return self.queries.delete_2d_detections_by_project_id(
                project_id=project_id
            )
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)
