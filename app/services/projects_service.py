from box import Box, BoxList
from loguru import logger
from pugsql.compiler import Module


class ProjectsService:
    def __init__(self, queries: Module):
        self.queries = queries

    def create(self, project_type):
        logger.debug(f"Creating project of type {project_type}")
        return self.queries.create_project(type=project_type)

    def get(self, project_id):
        return BoxList(self.queries.get_project(id=project_id))

    def list(self, row_count=10, offset=0):
        return BoxList(self.queries.get_projects(row_count=row_count, offset=offset))

    # def update(self, project_id, project):
    #     return self.queries.update_project(self.db, project_id, project)

    def delete(self, project_id):
        return self.queries.delete_project(id=project_id)
