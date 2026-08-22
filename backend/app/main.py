import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json

from backend.app.config import settings
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.models.models import User, Workspace, Project, Source, Collector, Watchlist, WatchlistItem
from backend.app.routes import auth, sources, collectors, repairs, market, alerts, health, demo_site
from backend.app.routes.auth import get_password_hash

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="Tathya API Portal",
    description="Backend API services powering the Tathya self-healing web data pipeline platform.",
    version="1.0.0"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all endpoint routers
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(collectors.router)
app.include_router(repairs.router)
app.include_router(market.router)
app.include_router(alerts.router)
app.include_router(health.router)
app.include_router(demo_site.router)

@app.get("/api/v1/ping")
def ping():
    """
    Liveness probe endpoint.
    """
    return {"status": "online", "service": "tathya-backend", "env": settings.ENV}

def seed_initial_data(db: Session):
    """
    Seeds default administrative user, default workspace, project, watchlists,
    and collectors (both local controlled demo and Yahoo/Google settings).
    """
    # 1. Create Default Admin User
    admin_email = "admin@tathya.io"
    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        logger.info("Seeding database with default administration account...")
        admin = User(
            email=admin_email,
            hashed_password=get_password_hash("tathya_admin_2026"),
            full_name="Lead Data Engineer",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        # 2. Create Default Workspace
        workspace = Workspace(
            name="Primary Workspace",
            owner_id=admin.id
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

        # 3. Create Default Project
        project = Project(
            name="Market Operations",
            workspace_id=workspace.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # 4. Create Sources
        # Source A: Controlled Demo target served locally
        demo_source = Source(
            name="Tathya Controlled Feed",
            url="http://localhost:8000/api/v1/demo-site/target",
            type="demo",
            project_id=project.id
        )
        # Source B: Yahoo Finance News
        yahoo_source = Source(
            name="Yahoo Finance Live",
            url="https://finance.yahoo.com/news/",
            type="news",
            project_id=project.id
        )
        # Source C: Google News Feed
        google_source = Source(
            name="Google News Feed",
            url="https://news.google.com/rss",
            type="news",
            project_id=project.id
        )
        db.add_all([demo_source, yahoo_source, google_source])
        db.commit()
        db.refresh(demo_source)
        db.refresh(yahoo_source)
        db.refresh(google_source)

        # 5. Create Collectors
        # Collector A: Local Controlled Demo Scraper
        demo_schema = {
            "symbol": "required",
            "headline": "required",
            "timestamp": "required",
            "category": "optional",
            "url": "required"
        }
        demo_selectors = {
            "row_container": ".market-event",
            "symbol": ".symbol",
            "headline": ".headline",
            "timestamp": ".timestamp",
            "category": ".category",
            "url": "a.url"
        }
        demo_collector = Collector(
            name="Local Demo Scraper",
            source_id=demo_source.id,
            status="UNKNOWN",
            active_schema=json.dumps(demo_schema),
            selector_mapping=json.dumps(demo_selectors),
            health_score=100.0
        )

        # Collector B: Yahoo Scraper
        yahoo_schema = {
            "headline": "required",
            "timestamp": "required",
            "url": "required"
        }
        # Selector map targets standard Yahoo feed tags
        yahoo_selectors = {
            "row_container": "section.substream",
            "headline": "h3",
            "timestamp": ".publishing",
            "url": "a"
        }
        yahoo_collector = Collector(
            name="Yahoo News Scraper",
            source_id=yahoo_source.id,
            brightdata_collector_id=None,  # Configured by user
            status="UNKNOWN",
            active_schema=json.dumps(yahoo_schema),
            selector_mapping=json.dumps(yahoo_selectors),
            health_score=100.0
        )

        # Collector C: Google News RSS Scraper
        google_schema = {
            "headline": "required",
            "timestamp": "required",
            "url": "required"
        }
        google_selectors = {
            "row_container": "item",
            "headline": "title",
            "timestamp": "pubDate",
            "url": "link"
        }
        google_collector = Collector(
            name="Google News Scraper",
            source_id=google_source.id,
            brightdata_collector_id=None,  # Configured by user
            status="UNKNOWN",
            active_schema=json.dumps(google_schema),
            selector_mapping=json.dumps(google_selectors),
            health_score=100.0
        )

        db.add_all([demo_collector, yahoo_collector, google_collector])
        db.commit()

        # 6. Create Watchlist for Admin
        watchlist = Watchlist(
            name="Default Watchlist",
            user_id=admin.id
        )
        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)

        # Add initial tracking symbols
        symbols = ["TCS", "RELIANCE", "INFY"]
        for s in symbols:
            item = WatchlistItem(
                watchlist_id=watchlist.id,
                symbol=s
            )
            db.add(item)
        db.commit()
        logger.info("Database seeding successfully completed.")

# Run Database Initialization
try:
    logger.info("Initializing relational database tables...")
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    seed_initial_data(db_session)
    db_session.close()
except Exception as db_err:
    logger.error(f"Error during database initialization/seeding: {db_err}")
