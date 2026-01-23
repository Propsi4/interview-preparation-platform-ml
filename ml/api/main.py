"""FastAPI application entrypoint."""

from typing import List, AsyncGenerator
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import uvicorn

from ml.api.routes.chat_history import router as chat_history_router
from ml.api.routes.scrapers import router as scrapers_router
from ml.api.schemas import HealthResponse
from ml.config.api import api_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan function to check health at startup."""
    from ml.conversation_history.manager import ConversationHistoryManager
    manager = ConversationHistoryManager()
    services_health: List[bool] = [
        await manager.check_health(),
    ]
    app.state.health_ok = all(services_health)
    yield

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
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Return service health status, using info set at startup."""
    health_ok = getattr(request.app.state, "health_ok", False)
    if health_ok:
        return HealthResponse(status="ok")
    else:
        return HealthResponse(status="error")

app.include_router(scrapers_router, tags=["Scrapers"])
app.include_router(chat_history_router, tags=["Chat History"])


if __name__ == "__main__":
    uvicorn.run(
        app="ml.api.main:app",
        host=api_config.API_HOST,
        port=api_config.API_PORT,
        reload=api_config.RELOAD_ON_CODE_CHANGE,
    )
