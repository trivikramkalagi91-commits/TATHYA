import json
import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.db.session import get_db
from backend.app.routes.auth import get_current_user
from backend.app.models.models import User, Source, Collector, ScrapeRun, ScrapeRecord, HealthCheck, Repair, MarketEvent, Alert, Project
from backend.app.schemas.schemas import CollectorCreate, CollectorResponse, ScrapeRunResponse
from backend.app.services.scraper import scrape_url
from backend.app.services.health_engine import calculate_health_score
from backend.app.services.healing_engine import generate_repair_proposal
from backend.app.integrations.brightdata import BrightDataClient

router = APIRouter(prefix="/api/v1/collectors", tags=["collectors"])
logger = logging.getLogger(__name__)
brightdata_client = BrightDataClient()

@router.get("/", response_model=List[CollectorResponse])
def get_collectors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all scrapers/collectors in the user's active workspaces.
    """
    workspace_ids = [w.id for w in current_user.workspaces]
    projects = db.query(Project).filter(Project.workspace_id.in_(workspace_ids)).all()
    project_ids = [p.id for p in projects]
    sources = db.query(Source).filter(Source.project_id.in_(project_ids)).all()
    source_ids = [s.id for s in sources]
    
    collectors = db.query(Collector).filter(Collector.source_id.in_(source_ids)).all()
    
    # Format schemas for output
    result = []
    for c in collectors:
        result.append(CollectorResponse(
            id=c.id,
            name=c.name,
            source_id=c.source_id,
            brightdata_collector_id=c.brightdata_collector_id,
            status=c.status,
            active_schema=json.loads(c.active_schema),
            selector_mapping=json.loads(c.selector_mapping),
            last_run_at=c.last_run_at,
            records_collected=c.records_collected,
            health_score=c.health_score,
            last_repair_at=c.last_repair_at,
            created_at=c.created_at
        ))
    return result

@router.post("/", response_model=CollectorResponse, status_code=status.HTTP_201_CREATED)
def create_collector(
    collector_in: CollectorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new collector with a schema and selector configuration.
    """
    source = db.query(Source).filter(Source.id == collector_in.source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Verify workspace ownership
    project = db.query(Project).filter(Project.id == source.project_id).first()
    if project.workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    collector = Collector(
        name=collector_in.name,
        source_id=collector_in.source_id,
        brightdata_collector_id=collector_in.brightdata_collector_id,
        status="UNKNOWN",
        active_schema=json.dumps(collector_in.active_schema),
        selector_mapping=json.dumps(collector_in.selector_mapping),
        health_score=100.0,
        records_collected=0
    )
    db.add(collector)
    db.commit()
    db.refresh(collector)

    return CollectorResponse(
        id=collector.id,
        name=collector.name,
        source_id=collector.source_id,
        brightdata_collector_id=collector.brightdata_collector_id,
        status=collector.status,
        active_schema=json.loads(collector.active_schema),
        selector_mapping=json.loads(collector.selector_mapping),
        last_run_at=collector.last_run_at,
        records_collected=collector.records_collected,
        health_score=collector.health_score,
        last_repair_at=collector.last_repair_at,
        created_at=collector.created_at
    )

@router.get("/{collector_id}", response_model=CollectorResponse)
def get_collector(
    collector_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single collector's configuration.
    """
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")
        
    return CollectorResponse(
        id=collector.id,
        name=collector.name,
        source_id=collector.source_id,
        brightdata_collector_id=collector.brightdata_collector_id,
        status=collector.status,
        active_schema=json.loads(collector.active_schema),
        selector_mapping=json.loads(collector.selector_mapping),
        last_run_at=collector.last_run_at,
        records_collected=collector.records_collected,
        health_score=collector.health_score,
        last_repair_at=collector.last_repair_at,
        created_at=collector.created_at
    )

def tag_symbols(headline: str) -> List[str]:
    headline_upper = headline.upper()
    symbols = []
    # Match symbols or common names
    mapping = {
        "TCS": ["TCS", "TATA CONSULTANCY"],
        "RELIANCE": ["RELIANCE", "RIL", "JIO"],
        "INFY": ["INFOSYS", "INFY"],
        "PAYTM": ["PAYTM", "ONE97"],
        "BHARTIARTL": ["BHARTIARTL", "AIRTEL"],
        "TATASTEEL": ["TATASTEEL", "TATA STEEL"],
        "BAJFINANCE": ["BAJFINANCE", "BAJAJ FINANCE"],
        "AAPL": ["AAPL", "APPLE"],
        "TSLA": ["TSLA", "TESLA"]
    }
    for sym, keywords in mapping.items():
        for kw in keywords:
            if kw in headline_upper:
                symbols.append(sym)
                break
    return symbols

@router.post("/{collector_id}/run")
async def run_collector(
    collector_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes the scraper. Parses HTML using current selectors, runs the health engine to 
    detect schema degradation, and triggers self-healing proposal generation if fields are missing.
    """
    collector = db.query(Collector).filter(Collector.id == collector_id).first()
    if not collector:
        raise HTTPException(status_code=404, detail="Collector not found")

    schema = json.loads(collector.active_schema)
    selectors = json.loads(collector.selector_mapping)
    source = collector.source

    records = []
    html_excerpt = ""
    err_msg = ""
    run_status = "SUCCESS"

    # Determine the Bright Data Collector ID to use
    brightdata_id = collector.brightdata_collector_id
    if not brightdata_id or not brightdata_id.strip():
        if "yahoo" in source.url.lower():
            brightdata_id = settings.DEFAULT_YAHOO_COLLECTOR_ID
        elif "google" in source.url.lower():
            brightdata_id = settings.DEFAULT_GOOGLE_COLLECTOR_ID

    # Check if we should run in Real Mode via Bright Data API
    use_brightdata = (
        brightdata_id is not None
        and brightdata_id.strip() != ""
        and brightdata_client.is_configured
        # For our local demo-target URL, we force local scraping so it is testable locally
        and "demo-site/target" not in source.url
    )

    if use_brightdata:
        # Trigger real Bright Data Scraping
        snapshot_id, err_msg = await brightdata_client.trigger_run(
            brightdata_id,
            source.url
        )
        if snapshot_id:
            # Poll the dataset API for the resulting rows
            brightdata_records, poll_err = await brightdata_client.poll_dataset(snapshot_id)
            if brightdata_records:
                records = brightdata_records
                html_excerpt = f"Bright Data Dataset Snapshot: {snapshot_id}"
            else:
                err_msg = poll_err or "Timeout retrieving Bright Data dataset"
        
        if err_msg:
            run_status = "FAILED"
            logger.error(f"Bright Data scrape failed: {err_msg}")
    else:
        # Run Local HTML/BeautifulSoup parsing
        records, html_excerpt, err_msg = await scrape_url(source.url, selectors, schema)
        if err_msg:
            run_status = "FAILED"

    # Evaluate health of the scraped output
    health_score, health_status, health_details = calculate_health_score(records, schema)
    
    if run_status == "FAILED" or health_status == "FAILED":
        run_status = "FAILED"
    elif health_status == "DEGRADED":
        run_status = "DEGRADED"

    # Create ScrapeRun record
    scrape_run = ScrapeRun(
        collector_id=collector.id,
        records_count=len(records),
        health_score=health_score,
        raw_html_excerpt=html_excerpt,
        status=run_status
    )
    db.add(scrape_run)
    db.commit()
    db.refresh(scrape_run)

    # Insert individual records
    for r in records:
        record_entry = ScrapeRecord(
            scrape_run_id=scrape_run.id,
            data=json.dumps(r)
        )
        db.add(record_entry)

    # Log health check details
    health_check = HealthCheck(
        collector_id=collector.id,
        scrape_run_id=scrape_run.id,
        health_score=health_score,
        status=health_status,
        details=json.dumps(health_details)
    )
    db.add(health_check)

    # Trigger Self-Healing failure detection if degraded or failed
    repair_proposal_id = None
    if health_status in ["DEGRADED", "FAILED"]:
        # Find the last 100% healthy run's records for alignment reference
        last_healthy_run = db.query(ScrapeRun).filter(
            ScrapeRun.collector_id == collector.id,
            ScrapeRun.health_score == 100.0
        ).order_by(ScrapeRun.id.desc()).first()
        last_healthy_records = []
        if last_healthy_run:
            recs = db.query(ScrapeRecord).filter(ScrapeRecord.scrape_run_id == last_healthy_run.id).all()
            last_healthy_records = [json.loads(r.data) for r in recs]
        else:
            # Fallback if no run is stored, feed mock history data matching structure to start
            last_healthy_records = [
                {
                    "symbol": "TCS",
                    "headline": "TCS expands partnership with Google Cloud for generative AI solutions.",
                    "timestamp": "2026-08-20T10:42:00Z",
                    "category": "Corporate",
                    "url": "https://example.com/tcs-google-ai"
                }
            ]

        # Fetch actual page content of the broken site run
        # For Bright Data we scrape the raw local URL since we need structural HTML mapping
        _, full_html, _ = await scrape_url(source.url, {}, {}) 
        
        # Generate the selector proposal
        proposed_mapping, explanation = generate_repair_proposal(
            full_html or html_excerpt,
            selectors,
            schema,
            last_healthy_records
        )

        missing_fields = ", ".join(health_details.get("completely_missing_required", [])) or "None"

        if proposed_mapping:
            # File a Repair Proposal
            repair = Repair(
                collector_id=collector.id,
                source_id=source.id,
                failure_reason=f"Field extraction health dropped to {health_score}%. Missing: {missing_fields}",
                missing_fields=missing_fields,
                proposed_selectors=json.dumps(proposed_mapping),
                status="PENDING_APPROVAL",
                before_health=health_score,
                verification_details=explanation
            )
            db.add(repair)
            db.commit()
            db.refresh(repair)
            repair_proposal_id = repair.id

            # Trigger a system warning Alert
            alert = Alert(
                title=f"Scraper Degradation: {collector.name}",
                description=f"Scraper health fell to {health_score}%. Missing fields: {missing_fields}. Self-healing has generated a repair proposal.",
                severity="WARNING" if health_status == "DEGRADED" else "CRITICAL",
                type="SCRAPER_FAIL",
                symbol=None,
                source_id=source.id
            )
            db.add(alert)
            db.commit()
    else:
        # Healthy run: Add market events downstream
        for r in records:
            symbol = r.get("symbol")
            headline = r.get("headline")
            url = r.get("url")
            timestamp = r.get("timestamp")
            
            matched_symbols = []
            if symbol:
                matched_symbols = [symbol.upper()]
            elif headline:
                matched_symbols = tag_symbols(headline)
                if not matched_symbols:
                    matched_symbols = ["GENERAL"]
                    
            for sym in matched_symbols:
                if sym and headline:
                    # Add to verified market data feed if not already existing
                    exists = db.query(MarketEvent).filter(
                        MarketEvent.company_symbol == sym,
                        MarketEvent.headline == headline
                    ).first()
                    
                    if not exists:
                        try:
                            pub_time = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        except Exception:
                            pub_time = datetime.datetime.utcnow()

                        market_event = MarketEvent(
                            source_name=source.name,
                            source_url=url or source.url,
                            company_symbol=sym,
                            headline=headline,
                            category=r.get("category", "general"),
                            publish_time=pub_time,
                            verification_status="VERIFIED"
                        )
                        db.add(market_event)
        
        # Trigger an alert on scraper recovery if it was degraded
        if collector.status in ["DEGRADED", "FAILED"]:
            alert = Alert(
                title=f"Scraper Restored: {collector.name}",
                description=f"Scraper health recovered to 100% after selector repair execution.",
                severity="INFO",
                type="SCRAPER_REPAIRED",
                source_id=source.id
            )
            db.add(alert)

    # Update Collector health and stats
    collector.status = health_status
    collector.health_score = health_score
    collector.last_run_at = datetime.datetime.utcnow()
    collector.records_collected += len(records)
    db.commit()

    return {
        "run_id": scrape_run.id,
        "records_count": len(records),
        "health_score": health_score,
        "status": health_status,
        "error": err_msg,
        "repair_proposal_id": repair_proposal_id
    }
