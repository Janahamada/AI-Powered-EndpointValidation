"""Aggregates every v1 router under a single APIRouter."""

from fastapi import APIRouter

from app.api.v1 import auth, blueprint, chat, dashboard, endpoints, reports, system

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(endpoints.router)
api_router.include_router(chat.router)
api_router.include_router(reports.router)
api_router.include_router(system.router)
api_router.include_router(blueprint.router)
