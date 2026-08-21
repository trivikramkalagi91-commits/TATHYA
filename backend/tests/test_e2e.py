import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app, seed_initial_data
from backend.app.db.session import Base, get_db
from backend.app.models.models import Collector, ScrapeRun, Repair, User

# Create a test SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tathya.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_initial_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_self_healing_e2e_workflow():
    client = TestClient(app)

    # 1. Login to get token
    login_response = client.post("/api/v1/auth/login", json={
        "email": "admin@tathya.io",
        "password": "tathya_admin_2026"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get the local demo collector
    collectors_response = client.get("/api/v1/collectors/", headers=headers)
    assert collectors_response.status_code == 200
    collectors = collectors_response.json()
    demo_collector = next(c for c in collectors if c["name"] == "Local Demo Scraper")
    c_id = demo_collector["id"]

    # 3. Ensure target is in Version A and run scraper (should be 100% healthy)
    client.post("/api/v1/demo-site/layout", json={"version": "A"})
    run_response = client.post(f"/api/v1/collectors/{c_id}/run", headers=headers)
    assert run_response.status_code == 200
    run_data = run_response.json()
    assert run_data["health_score"] == 100.0
    assert run_data["status"] == "HEALTHY"
    assert run_data["records_count"] == 5

    # 4. Toggle target site to Version B (structural change)
    toggle_response = client.post("/api/v1/demo-site/layout", json={"version": "B"})
    assert toggle_response.status_code == 200

    # 5. Run scraper again (should fail/degrade and trigger repair proposal)
    run_response_b = client.post(f"/api/v1/collectors/{c_id}/run", headers=headers)
    assert run_response_b.status_code == 200
    run_data_b = run_response_b.json()
    assert run_data_b["health_score"] == 0.0
    assert run_data_b["status"] == "FAILED"
    assert run_data_b["repair_proposal_id"] is not None
    proposal_id = run_data_b["repair_proposal_id"]

    # 6. Fetch repair details and verify proposal content
    repair_response = client.get(f"/api/v1/repairs/{proposal_id}", headers=headers)
    assert repair_response.status_code == 200
    repair_data = repair_response.json()
    assert repair_data["status"] == "PENDING_APPROVAL"
    assert "row_container" in repair_data["proposed_selectors"]

    # 7. Approve the repair proposal
    approve_response = client.post(f"/api/v1/repairs/{proposal_id}/approve", headers=headers)
    assert approve_response.status_code == 200
    approve_data = approve_response.json()
    assert approve_data["repair_status"] == "REPAIRED"
    assert approve_data["new_health_score"] == 100.0

    # 8. Check that collector is now healthy and has the updated selector config
    collector_final = client.get(f"/api/v1/collectors/{c_id}", headers=headers).json()
    assert collector_final["status"] == "HEALTHY"
    assert collector_final["selector_mapping"]["row_container"] == "article.event-card"
    assert collector_final["selector_mapping"]["symbol"] == "attr:data-symbol"
