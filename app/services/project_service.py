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

    def list(self, row_count=10, offset=0):
        results = self.queries.get_projects(row_count=row_count, offset=offset)
        results = delete_fields(["is_deleted"], rows=results)
        return results

    # def update(self, project_id, project):
    #     return self.queries.update_project(self.db, project_id, project)

    def delete(self, id):
        return self.queries.delete_project(id=id)
