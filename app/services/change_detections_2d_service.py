from pugsql.compiler import Module

from .projects_service import ProjectService


class ChangeDetections2DService:
    def __init__(self, queries: Module):
        self.queries = queries
        self.project_service = ProjectService(queries)

    def create(self, project_id=None, **change_detection):
        if project_id:
            project = self.project_service.get(project_id)
            if not project:
                msg = f"Project with id {project_id} does not exist"
                raise ValueError(msg)
        else:
            project_id = self.project_service.create(type="2d_detection")

        return self.queries.create_2d_change_detection(**change_detection)

    def get(self, *, change_detection_id=None, project_id=None):
        if change_detection_id:
            return self.queries.get_change_detection_2d(id=change_detection_id)
        elif project_id:
            return self.queries.get_change_detections_2d_by_project_id(
                project_id=project_id
            )
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)

    def delete(self, change_detection_id):
        return self.queries.delete_change_detection_2d(id=change_detection_id)
