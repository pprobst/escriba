"""Application entry point."""

from fastapi import FastAPI

from app.api.routes import setup_routes
from app.core.config import settings
from app.core.logger import log


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
    )

    # Setup routes
    setup_routes(app)

    log.info(f"Application {settings.app_title} initialized")
    return app


app = create_app()
