from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.logging import configure_logging
from app.db import close_client, ensure_indexes, ping
from app.modules.adjustments.router import router as adjustments_router
from app.modules.admins.router import router as admins_router
from app.modules.advances.router import router as advances_router
from app.modules.attendance.router import router as attendance_router
from app.modules.auth.router import router as auth_router
from app.modules.deductions.router import router as deductions_router
from app.modules.expenses.router import router as expenses_router
from app.modules.labourers.router import router as labourers_router
from app.modules.payments.router import router as payments_router
from app.modules.reports.router import router as reports_router
from app.modules.sites.router import router as sites_router
from app.modules.wages.router import router as wages_router
from app.modules.wall_calculations.router import router as wall_calculations_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.debug)
    await ensure_indexes()
    yield
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)

    app.include_router(auth_router)
    app.include_router(admins_router)
    app.include_router(labourers_router)
    app.include_router(sites_router)
    app.include_router(wages_router)
    app.include_router(attendance_router)
    app.include_router(expenses_router)
    app.include_router(advances_router)
    app.include_router(deductions_router)
    app.include_router(adjustments_router)
    app.include_router(payments_router)
    app.include_router(reports_router)
    app.include_router(wall_calculations_router)

    @app.get("/health")
    async def health() -> dict:
        db_ok = True
        try:
            await ping()
        except Exception:
            db_ok = False
        return {"status": "ok" if db_ok else "degraded", "database": db_ok}

    return app


app = create_app()
