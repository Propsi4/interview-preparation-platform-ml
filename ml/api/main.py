"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
import uvicorn

from ml.api.routes.scrapers import router
from ml.api.schemas import HealthResponse
from ml.config.api import api_config

app = FastAPI(
    title="Interview Preparation Platform API",
    root_path="/api/v1",
    version="0.1.0",
    description="API for the Interview Preparation Platform",
    debug=api_config.DEBUG,
    contact={
        "name": "Vadym Burylo",
        "email": "gaenday328@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Return service health status.

    Returns
    -------
    HealthResponse
        Health status payload.
    """
    return HealthResponse(status="ok")

app.include_router(router, tags=["scrapers"])


if __name__ == "__main__":
    uvicorn.run(
        app="ml.api.main:app",
        host=api_config.API_HOST,
        port=api_config.API_PORT,
        reload=api_config.RELOAD_ON_CODE_CHANGE,
    )
