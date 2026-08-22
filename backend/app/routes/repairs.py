import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db.session import get_db
from backend.app.routes.auth import get_current_user
from backend.app.models.models import User, Repair, Collector, Source, Project, Alert
from backend.app.schemas.schemas import RepairResponse
from backend.app.routes.collectors import run_collector

router = APIRouter(prefix="/api/v1/repairs", tags=["repairs"])

@router.get("/", response_model=List[RepairResponse])
def get_repairs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all self-healing repair tasks (both pending proposals and historic events).
    """
    workspace_ids = [w.id for w in current_user.workspaces]
    projects = db.query(Project).filter(Project.workspace_id.in_(workspace_ids)).all()
    project_ids = [p.id for p in projects]
    sources = db.query(Source).filter(Source.project_id.in_(project_ids)).all()
    source_ids = [s.id for s in sources]
    
    repairs = db.query(Repair).filter(Repair.source_id.in_(source_ids)).order_by(Repair.id.desc()).all()
    
    result = []
    for r in repairs:
        result.append(RepairResponse(
            id=r.id,
            collector_id=r.collector_id,
            source_id=r.source_id,
            failure_reason=r.failure_reason,
            missing_fields=r.missing_fields,
            proposed_selectors=json.loads(r.proposed_selectors) if r.proposed_selectors else {},
            started_at=r.started_at,
            completed_at=r.completed_at,
            status=r.status,
            before_health=r.before_health,
            after_health=r.after_health,
            recovered_fields=r.recovered_fields,
            verification_details=r.verification_details
        ))
    return result

@router.get("/{repair_id}", response_model=RepairResponse)
def get_repair(
    repair_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves detailed logs for a single self-healing action.
    """
    repair = db.query(Repair).filter(Repair.id == repair_id).first()
    if not repair:
        raise HTTPException(status_code=404, detail="Repair not found")
        
    # Verify ownership
    if repair.source.project.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    return RepairResponse(
        id=repair.id,
        collector_id=repair.collector_id,
        source_id=repair.source_id,
        failure_reason=repair.failure_reason,
        missing_fields=repair.missing_fields,
        proposed_selectors=json.loads(repair.proposed_selectors) if repair.proposed_selectors else {},
        started_at=repair.started_at,
        completed_at=repair.completed_at,
        status=repair.status,
        before_health=repair.before_health,
        after_health=repair.after_health,
        recovered_fields=repair.recovered_fields,
        verification_details=repair.verification_details
    )

@router.post("/{repair_id}/approve")
async def approve_repair_proposal(
    repair_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approves the selector repair proposal. The system updates the scraper selectors, 
    reruns the collection pipeline, verifies the health recovery, and marks it healthy.
    """
    repair = db.query(Repair).filter(
        Repair.id == repair_id,
        Repair.status == "PENDING_APPROVAL"
    ).first()
    
    if not repair:
        raise HTTPException(status_code=404, detail="Pending repair proposal not found or already processed.")
        
    # Verify ownership
    collector = repair.collector
    if collector.source.project.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 1. Update Repair State
    repair.status = "HEALING"
    db.commit()

    # 2. Apply proposed selector mappings to the collector (backing up the old mapping first)
    old_selectors_str = collector.selector_mapping
    proposed_mapping = json.loads(repair.proposed_selectors)
    collector.selector_mapping = json.dumps(proposed_mapping)
    collector.last_repair_at = datetime.datetime.utcnow()
    db.commit()

    # 3. Rerun Scraper to Verify
    verify_result = await run_collector(collector_id=collector.id, current_user=current_user, db=db)
    
    # 4. Verify output health
    new_health = verify_result.get("health_score", 0.0)
    new_status = verify_result.get("status", "FAILED")

    repair.completed_at = datetime.datetime.utcnow()
    repair.after_health = new_health

    if new_status == "HEALTHY":
        repair.status = "REPAIRED"
        repair.recovered_fields = repair.missing_fields
        repair.verification_details = f"Verified successfully. Health recovered from {repair.before_health}% to {new_health}%."
        
        # Trigger restoration Alert
        alert = Alert(
            title=f"Self-Healing Restored: {collector.name}",
            description=f"Self-healing successfully applied repair plan to {collector.name}. Pipeline running at 100% health.",
            severity="INFO",
            type="SCRAPER_REPAIRED",
            source_id=collector.source_id
        )
        db.add(alert)
    else:
        # Revert selectors in DB back to original degraded mapping
        collector.selector_mapping = old_selectors_str
        db.commit()
        
        repair.status = "FAILED"
        repair.verification_details = f"Verification failed. New health score is only {new_health}%. Scraper remains degraded."

    db.commit()

    return {
        "message": "Repair proposal processed",
        "repair_status": repair.status,
        "new_health_score": new_health,
        "details": repair.verification_details
    }
