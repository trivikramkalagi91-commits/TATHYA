from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings

# For SQLite, we need to allow access from multiple threads
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency generator for obtaining a database session.
    Ensures that sessions are properly closed after the request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
