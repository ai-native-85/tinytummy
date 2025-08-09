import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlalchemy import text
try:
    from app.database import engine as SYNC_ENGINE
except Exception:
    SYNC_ENGINE = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tinytummy")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: DB ping (sync engine)
    try:
        if SYNC_ENGINE is not None:
            with SYNC_ENGINE.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Database connected (sync engine)")
        else:
            logger.warning("DB engine not available; skipping ping")
    except Exception as e:
        logger.exception("❌ Database ping failed")
    yield
    # Shutdown: no-op
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="TinyTummy API",
        description="AI-powered Baby Nutrition Tracker API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware (match existing behavior broadly)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    # Routers: nutrition (and alias under /meals)
    try:
        from app.routes.nutrition import router as nutrition_router
        from app.routes.nutrition import meals_router as meals_nutrition_alias_router
        app.include_router(nutrition_router)
        app.include_router(meals_nutrition_alias_router)
    except Exception:
        pass

    # Gamification
    try:
        from app.routes.gamification import router as gamification_router
        app.include_router(gamification_router)
    except Exception:
        pass

    # Core routes (best-effort include)
    for mod, attr in [
        ("app.routes.auth", "router"),
        ("app.routes.children", "router"),
        ("app.routes.meals", "router"),
        ("app.routes.plans", "router"),
        ("app.routes.reports", "router"),
        ("app.routes.chat", "router"),
        ("app.routes.caregiver", "router"),
        ("app.routes.sync", "router"),
        ("app.routes.audio", "router"),
    ]:
        try:
            module = __import__(mod, fromlist=[attr])
            app.include_router(getattr(module, attr))
        except Exception:
            continue

    # Debug / health endpoints
    GIT_SHA = os.getenv("GIT_SHA", "unknown")

    @app.get("/version")
    def version():
        return {"git_sha": GIT_SHA}

    @app.get("/routes")
    def list_routes():
        return {"routes": [r.path for r in app.router.routes if isinstance(r, APIRoute)]}

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "tinytummy-api"}

    @app.get("/dbping")
    def dbping():
        if SYNC_ENGINE is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="No DB engine")
        with SYNC_ENGINE.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "mode": "sync"}

    return app


