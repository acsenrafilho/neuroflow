"""Aggregate API v1 routers."""

from fastapi import APIRouter

from neuroflow.api.v1 import datasets, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(datasets.router)
