from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database.base import Base
from app.database.connection import engine
import app.models

from app.routers import health
from app.routers import ai
from app.routers import conversation
from app.routers import analytics
from app.routers import dataset
from app.routers import ml
from app.routers import forecast


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="InsightForge AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(ValueError)
async def invalid_dataset(request: Request, error: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://insightforge-frontend-vmy3.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "InsightForge AI API is running",
        "status": "healthy",
        "docs": "/docs",
    }


# Routers
app.include_router(health.router)
app.include_router(ai.router)
app.include_router(conversation.router)
app.include_router(analytics.router)
app.include_router(dataset.router)
app.include_router(ml.router)
app.include_router(forecast.router)
