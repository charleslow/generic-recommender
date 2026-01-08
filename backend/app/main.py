"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from app.routers import recommend_router
from app.services.vector_search import vector_service
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load vector index on startup."""
    # Skip loading in local dev if GCS not configured
    if os.getenv("SKIP_INDEX_LOAD"):
        print("Skipping index load (SKIP_INDEX_LOAD=1)")
    else:
        await vector_service.initialize()
    yield


app = FastAPI(
    title="Generic Recommender API",
    description="A prompt-controlled recommendation system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # POC: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommend_router, tags=["recommendations"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Generic Recommender",
        "version": "0.1.0",
        "docs": "/docs",
    }
