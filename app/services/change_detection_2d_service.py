from pugsql.compiler import Module

from app.utils.table_funcs import delete_fields

from .project_service import ProjectService


class ChangeDetection2DService:
    def __init__(self, queries: Module):
        self.queries = queries
        self.project_service = ProjectService(queries)

    def create(
        self, image1_id, image2_id, project_id=None, project_name=None, **kwargs
    ):
        if project_id:
            project = self.project_service.get(project_id)
            if not project:
                msg = f"Project with id {project_id} does not exist"
                raise ValueError(msg)
        else:
            project_id = self.project_service.create(
                type="2d_detection", name=project_name, cover_image_id=image1_id
            )

        last_id = self.queries.create_2d_change_detection(
            image1_id=image1_id, image2_id=image2_id, project_id=project_id
        )
        if not last_id:
            msg = "Failed to create 2d change detection"
            raise ValueError(msg)

        return last_id, project_id

    def get(self, *, id=None, project_id=None):
        if id:
            return self.queries.get_change_detection_2d(id=id)
        elif project_id:
            return self.queries.get_change_detection_2d_by_project_id(
                project_id=project_id
            )
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)

    def delete(self, id):
        return self.queries.delete_change_detection_2d(id=id)
