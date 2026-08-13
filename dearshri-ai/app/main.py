"""DearShri-AI FastAPI application."""

from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from .routers.auth import router as auth_router
from .routers.journey import router as journey_router


class WelcomeResponse(BaseModel):
    """Response returned by the service welcome endpoint."""

    name: str
    message: str
    status: Literal["ready"]
    docs_url: str


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: Literal["healthy"]
    service: str
    timestamp: datetime


app = FastAPI(
    title="DearShri AI",
    summary="The DearShri-AI API",
    description="A FastAPI foundation for building DearShri-AI services.",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(journey_router)


@app.get("/", response_model=WelcomeResponse, tags=["service"])
async def welcome() -> WelcomeResponse:
    """Return a friendly service overview."""

    return WelcomeResponse(
        name="DearShri-AI",
        message="Welcome to DearShri-AI.",
        status="ready",
        docs_url="/docs",
    )


@app.get("/health", response_model=HealthResponse, tags=["service"])
async def health() -> HealthResponse:
    """Report whether the API is ready to receive requests."""

    return HealthResponse(
        status="healthy",
        service="DearShri-AI",
        timestamp=datetime.now(UTC),
    )