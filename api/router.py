from fastapi import APIRouter
from api.routes import integration
from api.routes import path

api_router = APIRouter()
api_router.include_router(integration.router, tags=["telex_integration_json"])
api_router.include_router(path.router, tags=["network_health_path"])