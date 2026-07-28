"""Aggregates every v1 router under a single APIRouter."""

from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    blueprint,
    chat,
    dashboard,
    endpoints,
    findings,
    reports,
    system,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(endpoints.router)
api_router.include_router(chat.router)
api_router.include_router(reports.router)
api_router.include_router(system.router)
api_router.include_router(blueprint.router)
api_router.include_router(audit.router)
api_router.include_router(findings.router)
