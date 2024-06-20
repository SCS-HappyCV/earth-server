from pugsql.compiler import Module

from .projects_service import ProjectsService


class Detections2DService:
    def __init__(self, queries: Module):
        self.queries = queries
        self.project_service = ProjectsService(queries)

    def create(self, project_id=None, **detection):
        if project_id:
            project = self.project_service.get(project_id)
            if not project:
                msg = f"Project with id {project_id} does not exist"
                raise ValueError(msg)
        else:
            project_id = self.project_service.create(type="2d_detection")

        return self.queries.create_2d_detection(**detection)

    def get(self, *, detection_id=None, project_id=None):
        if detection_id:
            return self.queries.get_detection_2d(id=detection_id)
        elif project_id:
            return self.queries.get_detections_2d_by_project_id(project_id=project_id)
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)

    def delete(self, detection_id):
        return self.queries.delete_detection_2d(id=detection_id)
