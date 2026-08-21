import datetime
import hashlib
import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from backend.app.db.session import get_db
from backend.app.config import settings
import json
from backend.app.models.models import User, Workspace, Project, Source, Collector, Watchlist, WatchlistItem
from backend.app.schemas.schemas import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login-oauth2")

def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    db_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{db_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt_hex, hash_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        db_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return db_hash.hex() == hash_hex
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user and automatically spins up their first workspace and project.
    """
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Provision first Workspace
    workspace = Workspace(
        name=f"{user.full_name or 'User'}'s Workspace",
        owner_id=user.id
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    # Provision first Project
    project = Project(
        name="Market Intelligence Feed",
        workspace_id=workspace.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Seed default data sources for the new project
    demo_source = Source(
        name="Tathya Controlled Feed",
        url="http://localhost:8000/api/v1/demo-site/target",
        type="demo",
        project_id=project.id
    )
    yahoo_source = Source(
        name="Yahoo Finance Live",
        url="https://finance.yahoo.com/news/",
        type="news",
        project_id=project.id
    )
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

    # Seed default collectors
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

    yahoo_schema = {
        "headline": "required",
        "timestamp": "required",
        "url": "required"
    }
    yahoo_selectors = {
        "row_container": "section.substream",
        "headline": "h3",
        "timestamp": ".publishing",
        "url": "a"
    }
    yahoo_collector = Collector(
        name="Yahoo News Scraper",
        source_id=yahoo_source.id,
        status="UNKNOWN",
        active_schema=json.dumps(yahoo_schema),
        selector_mapping=json.dumps(yahoo_selectors),
        health_score=100.0
    )

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
        status="UNKNOWN",
        active_schema=json.dumps(google_schema),
        selector_mapping=json.dumps(google_selectors),
        health_score=100.0
    )
    db.add_all([demo_collector, yahoo_collector, google_collector])
    db.commit()

    # Seed default watchlist
    watchlist = Watchlist(
        name="Default Watchlist",
        user_id=user.id
    )
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)

    # Seed initial watchlist symbols
    symbols = ["TCS", "RELIANCE", "INFOSYS"]
    for s in symbols:
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol=s
        )
        db.add(item)
    db.commit()

    return user

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates user and returns a JWT access token.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-oauth2", response_model=Token)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login for Swagger UI test logins.
    """
    # FastAPI OAuth2PasswordRequestForm maps credentials to username and password
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently logged-in user profile.
    """
    return current_user
