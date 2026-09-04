from fastapi import APIRouter
from app.api import auth, devices, users, cards, logs, stats

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(cards.router, prefix="/cards", tags=["Cards"])
api_router.include_router(logs.router, prefix="/logs", tags=["Access Logs"])
api_router.include_router(stats.router, prefix="/stats", tags=["Stats"])
