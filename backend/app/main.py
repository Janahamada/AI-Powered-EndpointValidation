"""
FastAPI application factory.

Mounts the v1 API, configures CORS for the SPA, sets up logging, and exposes
a health check. Business logic lives in services/validators — this module is
wiring only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.repositories import audit_repo, finding_state_repo

configure_logging()
logger = get_logger("app")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="AI Cyber Assurance Platform API — validates "
        "Antivirus, EDR, Firewall and BitLocker controls against an assurance "
        "blueprint and explains findings with grounded recommendations.",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # The audit trail was added after the seed scripts, so make sure its table
    # exists on databases that predate it. Creates only — never drops.
    audit_repo.ensure_table()
    finding_state_repo.ensure_table()

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}

    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "app": settings.APP_NAME,
            "docs": "/docs",
            "api": settings.API_V1_PREFIX,
        }

    logger.info("%s initialised (env=%s)", settings.APP_NAME, settings.ENVIRONMENT)
    return app


app = create_app()
