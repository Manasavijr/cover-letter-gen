"""AI Cover Letter Generator — FastAPI Backend"""
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from backend.app.api.routes import generate, health
from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Cover Letter Generator API...")
    from backend.ml.matcher import get_model
    get_model()
    logger.info(f"Embedding model loaded. Ollama: {settings.OLLAMA_BASE_URL}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="AI Cover Letter Generator",
    description="Personalized cover letter generation using LangChain + Ollama + FAISS semantic matching.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(generate.router, prefix="/api/v1", tags=["Generate"])


@app.get("/")
async def root():
    return {"service": "AI Cover Letter Generator", "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {"generate": "POST /api/v1/generate", "regenerate": "POST /api/v1/regenerate", "tones": "GET /api/v1/tones"}}


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
