from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict

router = APIRouter(prefix="/api/v1/demo-site", tags=["demo-site"])

# In-memory storage for current active version of the demo website
# Version "A" represents the healthy structure.
# Version "B" represents the shifted/broken structure.
site_state = {
    "version": "A"
}

class SetLayoutRequest(BaseModel):
    version: str  # "A" or "B"

# Dynamic market headlines to render
MARKET_NEWS_DATA = [
    {
        "symbol": "TCS",
        "headline": "TCS expands partnership with Google Cloud for generative AI solutions.",
        "timestamp": "2026-08-20T10:42:00Z",
        "category": "Corporate",
        "url": "https://example.com/tcs-google-ai"
    },
    {
        "symbol": "RELIANCE",
        "headline": "Reliance announces major green hydrogen investment in Gujarat.",
        "timestamp": "2026-08-20T10:39:00Z",
        "category": "Announcement",
        "url": "https://example.com/reliance-green-hydrogen"
    },
    {
        "symbol": "INFOSYS",
        "headline": "Infosys beats earnings estimates with 8% YoY revenue growth.",
        "timestamp": "2026-08-20T10:35:00Z",
        "category": "Results",
        "url": "https://example.com/infosys-q1-results"
    },
    {
        "symbol": "TATASTEEL",
        "headline": "Tata Steel starts operations of new electric arc furnace plant.",
        "timestamp": "2026-08-20T10:15:00Z",
        "category": "Industrial",
        "url": "https://example.com/tata-steel-eaf"
    },
    {
        "symbol": "HDFCBANK",
        "headline": "HDFC Bank net interest income rises 12% in quarterly update.",
        "timestamp": "2026-08-20T10:02:00Z",
        "category": "Results",
        "url": "https://example.com/hdfc-bank-nii"
    }
]

@router.get("/layout")
def get_layout_version():
    """
    Returns the current structure version (A or B) of the controlled website.
    """
    return site_state

@router.post("/layout")
def update_layout_version(payload: SetLayoutRequest):
    """
    Toggles the active layout version (A or B) of the controlled website.
    """
    if payload.version not in ["A", "B"]:
        raise HTTPException(status_code=400, detail="Invalid version. Must be 'A' or 'B'")
    site_state["version"] = payload.version
    return {"message": f"Demo target website layout version updated to {payload.version}", "version": site_state["version"]}

@router.get("/target", response_class=HTMLResponse)
def get_demo_target_site():
    """
    Renders the HTML of the mock market site.
    Depending on the state, it will serve either Version A (traditional selector structure)
    or Version B (semantic tags with restructured metadata fields) to simulate DOM changes.
    """
    version = site_state["version"]
    
    html_content = ""
    if version == "A":
        # Traditional CSS class selectors
        items_html = ""
        for item in MARKET_NEWS_DATA:
            items_html += f"""
            <div class="market-event">
                <span class="symbol">{item['symbol']}</span>
                <h3 class="headline">{item['headline']}</h3>
                <span class="timestamp">{item['timestamp']}</span>
                <span class="category">{item['category']}</span>
                <a class="url" href="{item['url']}">Read Full Report</a>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tathya Demo Target Website - Version A</title>
            <style>
                body {{ font-family: monospace; background-color: #121212; color: #e0e0e0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                .market-event {{ background-color: #1e1e1e; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 4px; }}
                .symbol {{ font-weight: bold; color: #F59E0B; }}
                .headline {{ margin: 10px 0; font-size: 1.2rem; }}
                .timestamp {{ font-size: 0.8rem; color: #888; margin-right: 15px; }}
                .category {{ font-size: 0.8rem; background-color: #2e2e2e; padding: 2px 6px; border-radius: 2px; }}
                .url {{ display: block; margin-top: 10px; color: #3b82f6; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Tathya Controlled Market Feed (Version A - Standard CSS selectors)</h1>
                    <p>Current System State: <strong>HEALTHY SELECTORS ACTIVE</strong></p>
                </div>
                <div id="events-list">
                    {items_html}
                </div>
            </div>
        </body>
        </html>
        """
    else:
        # Version B: Structural and attribute-level semantic DOM changes
        items_html = ""
        for item in MARKET_NEWS_DATA:
            # Shift selectors: div.market-event -> article.event-card
            # symbol -> data-symbol attribute in article card
            # headline -> title class
            # timestamp -> time element
            # category -> type-tag class
            # url -> source-link class
            items_html += f"""
            <article class="event-card" data-symbol="{item['symbol']}">
                <div class="event-header">
                    <span class="type-tag">{item['category']}</span>
                    <time class="event-time" datetime="{item['timestamp']}">{item['timestamp']}</time>
                </div>
                <h2 class="title">{item['headline']}</h2>
                <a class="source-link" href="{item['url']}">Read Announcement</a>
            </article>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tathya Demo Target Website - Version B</title>
            <style>
                body {{ font-family: monospace; background-color: #121212; color: #e0e0e0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }}
                .event-card {{ background-color: #222222; border-left: 4px solid #D97706; padding: 15px; margin-bottom: 15px; }}
                .event-header {{ display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 8px; }}
                .type-tag {{ color: #a3a3a3; font-style: italic; }}
                .event-time {{ color: #737373; }}
                .title {{ font-size: 1.15rem; margin: 5px 0; font-weight: normal; color: #fafafa; }}
                .source-link {{ display: inline-block; margin-top: 5px; color: #fbbf24; text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Tathya Controlled Market Feed (Version B - Redesigned DOM layout)</h1>
                    <p>Current System State: <strong>DOM CHANGE DETECTED - SCRAPERS MAY FAIL</strong></p>
                </div>
                <div id="news-grid">
                    {items_html}
                </div>
            </div>
        </body>
        </html>
        """
    return html_content
