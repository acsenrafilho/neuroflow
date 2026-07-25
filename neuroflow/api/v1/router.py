"""Aggregate API v1 routers."""

from fastapi import APIRouter

from neuroflow.api.v1 import health, host, jobs, tools, workspaces
from neuroflow.models.schemas import ModuleInfo

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(host.router)
api_router.include_router(jobs.router)
api_router.include_router(tools.router)
api_router.include_router(workspaces.router)
api_router.add_api_route(
    "/modules",
    tools.list_processing_modules,
    methods=["GET"],
    tags=["tools"],
    response_model=list[ModuleInfo],
)
