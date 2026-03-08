"""
Text-to-CAD Backend Application
FastAPI-based API for natural language to CAD conversion
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import tasks, websocket
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME}...")
    yield
    # Shutdown
    print(f"👋 Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title="Text-to-CAD API",
    description="Natural language to STEP CAD model generation",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    return {
        "name": "Text-to-CAD API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
