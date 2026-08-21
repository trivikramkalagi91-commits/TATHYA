import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any, Dict, List

# Token & Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Workspace
class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceResponse(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Project
class ProjectBase(BaseModel):
    name: str
    workspace_id: int

class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Source
class SourceBase(BaseModel):
    name: str
    url: str
    type: str  # exchange, company_ir, news, regulatory, demo

class SourceCreate(SourceBase):
    project_id: int

class SourceResponse(SourceBase):
    id: int
    project_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Collector
class CollectorBase(BaseModel):
    name: str
    brightdata_collector_id: Optional[str] = None
    active_schema: Dict[str, str] = Field(..., description="Field names and their requirement type (required / optional)")
    selector_mapping: Dict[str, str] = Field(..., description="Target field to CSS selector/JSON pathway map")

class CollectorCreate(CollectorBase):
    source_id: int

class CollectorResponse(BaseModel):
    id: int
    name: str
    source_id: int
    brightdata_collector_id: Optional[str] = None
    status: str
    active_schema: Dict[str, str]
    selector_mapping: Dict[str, str]
    last_run_at: Optional[datetime.datetime] = None
    records_collected: int
    health_score: float
    last_repair_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ScrapeRunResponse(BaseModel):
    id: int
    collector_id: int
    run_at: datetime.datetime
    records_count: int
    health_score: float
    status: str

    class Config:
        from_attributes = True

# Repairs
class RepairResponse(BaseModel):
    id: int
    collector_id: int
    source_id: int
    failure_reason: str
    missing_fields: str
    proposed_selectors: Optional[Dict[str, str]] = None
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    status: str
    before_health: float
    after_health: float
    recovered_fields: Optional[str] = None
    verification_details: Optional[str] = None

    class Config:
        from_attributes = True

# Market Events
class MarketEventResponse(BaseModel):
    id: int
    source_name: str
    source_url: str
    company_symbol: str
    headline: str
    category: str
    publish_time: datetime.datetime
    scrape_time: datetime.datetime
    verification_status: str

    class Config:
        from_attributes = True

class OpportunitySignal(BaseModel):
    symbol: str
    opportunity_score: float
    headline: str
    source: str
    publish_time: datetime.datetime
    evidence_breakdown: Dict[str, Any]
    trade_scenario: Dict[str, Any]

class WhyMovedResponse(BaseModel):
    symbol: str
    price_change_pct: float
    possible_factors: List[Dict[str, Any]]
    evidence_status: str

# Watchlists
class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class WatchlistResponse(BaseModel):
    id: int
    name: str
    items: List[WatchlistItemResponse]

    class Config:
        from_attributes = True

class WatchlistCreate(BaseModel):
    name: str

class WatchlistSymbolAdd(BaseModel):
    symbol: str

# Alerts
class AlertResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    type: str
    symbol: Optional[str] = None
    source_id: Optional[int] = None
    read: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Dashboard Metrics
class DashboardMetrics(BaseModel):
    active_sources: int
    healthy_collectors: int
    degraded_collectors: int
    repairs_count: int
    records_collected: int
    avg_recovery_time_mins: float
