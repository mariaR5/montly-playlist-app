from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import auth

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the Monthly Playlist app",
    version="1.0.0",
)

app.include_router(auth.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Monthly Playlist API",
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }
