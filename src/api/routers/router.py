from fastapi import APIRouter

from api.routers import admin, analytics, health, territories, transactions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(transactions.router)
api_router.include_router(territories.router)
api_router.include_router(analytics.router)
api_router.include_router(admin.router)
