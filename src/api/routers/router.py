from fastapi import APIRouter

from api.routers import health

api_router = APIRouter()
api_router.include_router(health.router)
