from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import auth, search, playlist
from app.core.redis import get_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the Monthly Playlist app",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(playlist.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENVIRONMENT}
