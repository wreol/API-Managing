"""Main router aggregating all API route modules."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.keys import router as keys_router
from app.api.providers import router as providers_router
from app.api.usage import router as usage_router
from app.api.alerts import router as alerts_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(keys_router)
api_router.include_router(providers_router)
api_router.include_router(usage_router)
api_router.include_router(alerts_router)
