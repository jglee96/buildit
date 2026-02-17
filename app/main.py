from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers.projects import router as projects_router
from app.routers.rules import router as rules_router
from app.routers.runs import router as runs_router
from app.routers.users import router as users_router

app = FastAPI(title="buildit", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


app.include_router(users_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(runs_router, prefix="/api")
