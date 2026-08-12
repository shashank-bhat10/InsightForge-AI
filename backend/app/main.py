from fastapi import FastAPI
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


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="InsightForge AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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