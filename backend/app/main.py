import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.dataset_manager import dataset_manager

from app.api.routes_datasets import router as datasets_router
from app.api.routes_chat import router as chat_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_cleaning import router as cleaning_router
from app.api.routes_formulas import router as formulas_router
from app.api.routes_sql import router as sql_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_ml import router as ml_router
from app.api.routes_reports import router as reports_router
from app.api.routes_connectors import router as connectors_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("datapilot-ai")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing DataPilot AI Autonomous Analytics Platform...")
    # Generate initial sample dataset if no datasets exist
    try:
        if not dataset_manager.list_datasets():
            logger.info("Auto-generating default retail sales dataset...")
            dataset_manager.generate_sample_dataset("retail_sales", 5000)
    except Exception as e:
        logger.error(f"Error initializing sample dataset: {e}")
    yield
    logger.info("Shutting down DataPilot AI backend.")

app = FastAPI(
    title="DataPilot AI — Autonomous Data Analyst Platform",
    description="Production-grade AI-powered Autonomous Data Analytics Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(datasets_router)
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(cleaning_router)
app.include_router(formulas_router)
app.include_router(sql_router)
app.include_router(analytics_router)
app.include_router(ml_router)
app.include_router(reports_router)
app.include_router(connectors_router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "DataPilot AI Backend",
        "version": "1.0.0",
        "duckdb": "online",
        "llm_provider": settings.LLM_PROVIDER
    }

# Mount frontend production build if available
frontend_dist = settings.BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

