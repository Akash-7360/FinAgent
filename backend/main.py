import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models import entities # Register models with Base
from backend.app.api import auth, expenses, budgets, analytics, agent, alerts, reports
from backend.app.agent.proactive import ProactiveMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finagent")

# Initialize DB Tables on startup
Base.metadata.create_all(bind=engine)

# Scheduled Background Proactive Monitoring Job
def run_proactive_monitoring():
    logger.info("Executing scheduled proactive expense monitoring...")
    db = SessionLocal()
    try:
        monitor = ProactiveMonitor(db)
        users = db.query(entities.User).all()
        for u in users:
            alerts_gen = monitor.scan_user(u.id)
            if alerts_gen:
                logger.info(f"Generated {len(alerts_gen)} proactive alerts for user {u.email}")
    except Exception as e:
        logger.error(f"Error during proactive monitoring: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FinAgent Backend initializing...")
    # Run seed check or create default demo user
    db = SessionLocal()
    try:
        from backend.seed_data import seed_default_data
        seed_default_data(db)
    except Exception as e:
        logger.warning(f"Seeding notice: {e}")
    finally:
        db.close()

    try:
        scheduler.add_job(
            run_proactive_monitoring,
            "interval",
            minutes=settings.PROACTIVE_MONITOR_INTERVAL_MINUTES,
            id="proactive_monitor_job"
        )
        scheduler.start()
        logger.info(f"APScheduler active: scanning every {settings.PROACTIVE_MONITOR_INTERVAL_MINUTES} minutes.")
    except Exception as e:
        logger.warning(f"Could not start background scheduler: {e}")

    yield

    # Shutdown
    try:
        if scheduler.running:
            scheduler.shutdown()
    except Exception:
        pass
    logger.info("FinAgent Backend shut down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic Personal Expense Intelligence API",
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

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(budgets.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FinAgent API",
        "agent": "LangGraph Orchestrator",
        "ml_engine": "MultiLayer Isolation Forest & Z-Score"
    }
