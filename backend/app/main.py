from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, tasks, users
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API مدیریت وظایف با احراز هویت امن و مدیریت نشست.",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(tasks.router)

    @application.get("/health", tags=["Health"])
    def health_check():
        return {"status": "ok", "version": settings.app_version}

    return application


app = create_app()
