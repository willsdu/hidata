from fastapi import APIRouter
from hidata.app.routers.providers import router as providers_router


router = APIRouter()


router.include_router(providers_router)

__all__ = ["router"]