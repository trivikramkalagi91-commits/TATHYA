import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, Float
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    workspaces = relationship("Workspace", back_populates="owner")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="workspaces")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    workspace = relationship("Workspace", back_populates="projects")
    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    type = Column(String, default="exchange")  # exchange, company_ir, news, regulatory, demo
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="sources")
    collectors = relationship("Collector", back_populates="source", cascade="all, delete-orphan")
    repairs = relationship("Repair", back_populates="source", cascade="all, delete-orphan")

class Collector(Base):
    __tablename__ = "collectors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"))
    brightdata_collector_id = Column(String, nullable=True)
    status = Column(String, default="UNKNOWN")  # HEALTHY, DEGRADED, FAILED, UNKNOWN
    active_schema = Column(Text, nullable=False)  # JSON string mapping fields: type (e.g. required/optional)
    selector_mapping = Column(Text, nullable=False)  # JSON string of HTML selectors or JSON pathways
    last_run_at = Column(DateTime, nullable=True)
    records_collected = Column(Integer, default=0)
    health_score = Column(Float, default=100.0)
    last_repair_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    source = relationship("Source", back_populates="collectors")
    scrape_runs = relationship("ScrapeRun", back_populates="collector", cascade="all, delete-orphan")
    health_checks = relationship("HealthCheck", back_populates="collector", cascade="all, delete-orphan")
    repairs = relationship("Repair", back_populates="collector", cascade="all, delete-orphan")

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    collector_id = Column(Integer, ForeignKey("collectors.id"))
    run_at = Column(DateTime, default=datetime.datetime.utcnow)
    records_count = Column(Integer, default=0)
    health_score = Column(Float, default=100.0)
    raw_html_excerpt = Column(Text, nullable=True)
    status = Column(String, default="SUCCESS")  # SUCCESS, FAILED, DEGRADED

    collector = relationship("Collector", back_populates="scrape_runs")
    records = relationship("ScrapeRecord", back_populates="scrape_run", cascade="all, delete-orphan")

class ScrapeRecord(Base):
    __tablename__ = "scrape_records"

    id = Column(Integer, primary_key=True, index=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"))
    data = Column(Text, nullable=False)  # JSON representation of scraped data fields
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scrape_run = relationship("ScrapeRun", back_populates="records")

class HealthCheck(Base):
    __tablename__ = "health_checks"

    id = Column(Integer, primary_key=True, index=True)
    collector_id = Column(Integer, ForeignKey("collectors.id"))
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
    check_time = Column(DateTime, default=datetime.datetime.utcnow)
    health_score = Column(Float, default=100.0)
    status = Column(String, default="HEALTHY")  # HEALTHY, DEGRADED, FAILED
    details = Column(Text, nullable=True)  # JSON showing details of what fields failed/missing

    collector = relationship("Collector", back_populates="health_checks")

class Repair(Base):
    __tablename__ = "repairs"

    id = Column(Integer, primary_key=True, index=True)
    collector_id = Column(Integer, ForeignKey("collectors.id"))
    source_id = Column(Integer, ForeignKey("sources.id"))
    failure_reason = Column(String, nullable=False)
    missing_fields = Column(String, nullable=False)  # comma separated list
    proposed_selectors = Column(Text, nullable=True)  # JSON string of repaired selectors
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="PENDING_APPROVAL")  # PENDING_APPROVAL, HEALING, VERIFYING, REPAIRED, FAILED
    before_health = Column(Float, default=0.0)
    after_health = Column(Float, default=0.0)
    recovered_fields = Column(String, nullable=True)
    verification_details = Column(Text, nullable=True)

    collector = relationship("Collector", back_populates="repairs")
    source = relationship("Source", back_populates="repairs")

class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    company_symbol = Column(String, nullable=False, index=True)
    headline = Column(String, nullable=False)
    category = Column(String, default="general")
    publish_time = Column(DateTime, nullable=False)
    scrape_time = Column(DateTime, default=datetime.datetime.utcnow)
    raw_data_ref = Column(Text, nullable=True)  # JSON metadata representation
    normalized_at = Column(DateTime, default=datetime.datetime.utcnow)
    verification_status = Column(String, default="VERIFIED")  # VERIFIED, UNVERIFIED

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, default="Default Watchlist")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"))
    symbol = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    watchlist = relationship("Watchlist", back_populates="items")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="INFO")  # INFO, WARNING, CRITICAL
    type = Column(String, nullable=False)  # SCRAPER_FAIL, SCRAPER_REPAIRED, MARKET_EVENT, OPPORTUNITY
    symbol = Column(String, nullable=True, index=True)
    source_id = Column(Integer, nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
