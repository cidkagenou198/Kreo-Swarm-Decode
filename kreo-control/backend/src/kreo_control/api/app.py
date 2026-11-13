from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kreo_control.api.routes import assets, device, lighting, profiles, ambience


def create_app() -> FastAPI:
    """FastAPI application factory for Kreo Control."""
    app = FastAPI(
        title="Kreo Control Backend",
        description="Independent backend and HID transport for Kreo Swarm 75",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(device.router)
    app.include_router(lighting.router)
    app.include_router(assets.router)
    app.include_router(profiles.router)
    app.include_router(ambience.router)

    @app.get("/api/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "app": "kreo-control"}

    return app


app = create_app()

