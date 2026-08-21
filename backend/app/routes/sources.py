from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db.session import get_db
from backend.app.routes.auth import get_current_user
from backend.app.models.models import User, Source, Project, Workspace
from backend.app.schemas.schemas import SourceCreate, SourceResponse

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])

@router.get("/", response_model=List[SourceResponse])
def get_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all registered scraping sources belonging to the user's active workspaces.
    """
    # Fetch user's workspaces
    workspace_ids = [w.id for w in current_user.workspaces]
    # Fetch projects in those workspaces
    projects = db.query(Project).filter(Project.workspace_id.in_(workspace_ids)).all()
    project_ids = [p.id for p in projects]
    
    # Fetch sources linked to those projects
    sources = db.query(Source).filter(Source.project_id.in_(project_ids)).all()
    return sources

@router.post("/", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source(
    source_in: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registers a new data source under a specific project.
    """
    # Verify project ownership
    project = db.query(Project).filter(Project.id == source_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    workspace = db.query(Workspace).filter(
        Workspace.id == project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=403, detail="Not authorized to add sources to this project")

    db_source = Source(
        name=source_in.name,
        url=source_in.url,
        type=source_in.type,
        project_id=source_in.project_id
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches detailed configuration for a specific data source.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Verify ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == source.project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=403, detail="Not authorized to view this source")
        
    return source

@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a registered data source and all its child collectors.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Verify ownership
    workspace = db.query(Workspace).filter(
        Workspace.id == source.project.workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=403, detail="Not authorized to modify this source")
        
    db.delete(source)
    db.commit()
    return {"message": f"Source {source_id} successfully deleted."}
