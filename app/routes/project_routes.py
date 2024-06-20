from typing import ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import ProjectsService


def project_service_provider(state: State) -> ProjectsService:
    return ProjectsService(state.queries)


class ProjectController(Controller):
    path = "/project"
    dependencies: ClassVar = {
        "projects_service": Provide(project_service_provider, sync_to_thread=True)
    }

    @get(path="/", sync_to_thread=True)
    def get_projects(self, projects_service: ProjectsService) -> ResponseWrapper:
        logger.debug("Getting projects")

        projects = projects_service.list()
        logger.debug(f"Projects: {projects}")

        return ResponseWrapper(projects)

    @get(path="/{project_id:int}", sync_to_thread=True)
    def get_project(
        self, project_id: int, projects_service: ProjectsService
    ) -> ResponseWrapper:
        logger.debug(f"Getting project with id {project_id}")

        project = projects_service.get(project_id)
        logger.debug(f"Project: {project}")

        if not project:
            return Response(
                ResponseWrapper(
                    code=2, message=f"Project with id {project_id} not found"
                ),
                status_code=HTTP_404_NOT_FOUND,
            )
        return ResponseWrapper(project)

    @post(path="/", sync_to_thread=True)
    def create_project(
        self, data: dict, projects_service: ProjectsService
    ) -> ResponseWrapper | Response:
        logger.debug(f"Creating project with data {data}")

        project_id = projects_service.create(data["type"])

        if project_id:
            return ResponseWrapper(
                {"id": project_id}, message="Project created successfully"
            )
        return Response(
            ResponseWrapper(code=1, message="Failed to create project"),
            status_code=HTTP_404_NOT_FOUND,
        )

    @delete(path="/{project_id:int}", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete_project(
        self, project_id: int, projects_service: ProjectsService
    ) -> ResponseWrapper | Response:
        if projects_service.delete(project_id):
            return ResponseWrapper()
        return Response(
            ResponseWrapper(code=2, message=f"Project with id {project_id} not found"),
            status_code=HTTP_404_NOT_FOUND,
        )
