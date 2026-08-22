import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.session import get_db
from backend.app.routes.auth import get_current_user
from backend.app.models.models import User, Source, Collector, Repair, HealthCheck, ScrapeRun
from backend.app.schemas.schemas import DashboardMetrics

router = APIRouter(prefix="/api/v1/health", tags=["health"])

@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggregates database metrics to feed the top-level Overview dashboard indicators.
    """
    # Count Active Sources for the current user
    user_sources = db.query(Source).join(Project).join(Workspace).filter(Workspace.owner_id == current_user.id)
    active_sources = user_sources.count()

    # Count Scraper states for the current user
    user_collectors = db.query(Collector).join(Source).join(Project).join(Workspace).filter(Workspace.owner_id == current_user.id)
    healthy_collectors = db.query(Collector).join(Source).join(Project).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Collector.status == "HEALTHY"
    ).count()
    degraded_collectors = db.query(Collector).join(Source).join(Project).join(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Collector.status.in_(["DEGRADED", "FAILED"])
    ).count()

    # Count Total Repairs for the current user
    user_repairs = db.query(Repair).join(Collector).join(Source).join(Project).join(Workspace).filter(Workspace.owner_id == current_user.id)
    repairs_count = user_repairs.count()

    # Count Total Records scraped for the current user
    records_sum = db.query(func.sum(Collector.records_collected)).join(Source).join(Project).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).scalar() or 0

    # Calculate Average Recovery Time in minutes for the current user
    completed_repairs = user_repairs.filter(
        Repair.status == "REPAIRED",
        Repair.completed_at != None
    ).all()

    total_mins = 0.0
    for r in completed_repairs:
        diff = r.completed_at - r.started_at
        total_mins += diff.total_seconds() / 60.0

    avg_recovery = round(total_mins / len(completed_repairs), 1) if completed_repairs else 0.0

    return DashboardMetrics(
        active_sources=active_sources,
        healthy_collectors=healthy_collectors,
        degraded_collectors=degraded_collectors,
        repairs_count=repairs_count,
        records_collected=records_sum,
        avg_recovery_time_mins=avg_recovery
    )

@router.get("/history")
def get_health_checks_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns recent health status runs across the platform to populate the dashboard activity stream.
    """
    runs = db.query(ScrapeRun).join(Collector).join(Source).join(Project).join(Workspace).filter(
        Workspace.owner_id == current_user.id
    ).order_by(ScrapeRun.run_at.desc()).limit(15).all()
    
    result = []
    for run in runs:
        result.append({
            "id": run.id,
            "collector_name": run.collector.name,
            "source_name": run.collector.source.name,
            "run_at": run.run_at,
            "records_count": run.records_count,
            "health_score": run.health_score,
            "status": run.status
        })
    return result
