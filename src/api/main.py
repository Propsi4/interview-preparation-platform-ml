"""FastAPI application entrypoint."""

from typing import List, AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.api.routes.chat_history import router as chat_history_router
from src.api.routes.chat import router as chat_router
from src.api.routes.evaluation import router as evaluation_router
from src.api.routes.scrapers import router as scrapers_router
from src.api.routes.speech import router as speech_router
from src.api.schemas import StatusResponseSchema
from src.config.api import api_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Lifespan function to check health at startup."""
    from src.conversation_history.manager import ConversationHistoryManager

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=api_config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=StatusResponseSchema)
async def health(request: Request) -> StatusResponseSchema:
    """Return service health status, using info set at startup."""
    health_ok = getattr(request.app.state, "health_ok", False)
    if health_ok:
        return StatusResponseSchema(status="ok", message="Service is healthy")
    else:
        return StatusResponseSchema(status="error", message="Service is not healthy")


app.include_router(scrapers_router, prefix="/scrapers", tags=["Scrapers"])
app.include_router(chat_history_router, prefix="/conversation_history", tags=["Conversation History"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(speech_router, prefix="/speech", tags=["Speech"])
app.include_router(evaluation_router, prefix="/evaluation", tags=["Evaluation"])


if __name__ == "__main__":
    uvicorn.run(
        app="src.api.main:app",
        host=api_config.API_HOST,
        port=api_config.API_PORT,
        reload=api_config.RELOAD_ON_CODE_CHANGE,
    )
