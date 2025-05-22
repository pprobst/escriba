"""Setup application routes."""

from fastapi import APIRouter

from app.api.endpoints import router as api_router


def setup_routes(app) -> None:
    """Configure routes for the application.

    Args:
        app: The FastAPI application instance
    """
    # Create main router
    main_router = APIRouter()

    # Include API endpoints
    main_router.include_router(api_router)

    # Include main router in app
    app.include_router(main_router)
