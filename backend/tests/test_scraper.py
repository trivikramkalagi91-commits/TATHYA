import pytest
import json
from backend.app.services.scraper import parse_html_content
from backend.app.services.health_engine import calculate_health_score, diff_selector_mappings
from backend.app.services.healing_engine import generate_repair_proposal

# Sample HTML structures
HTML_VERSION_A = """
<!DOCTYPE html>
<html>
<body>
    <div class="market-event">
        <span class="symbol">TCS</span>
        <h3 class="headline">New AI investment announced</h3>
        <span class="timestamp">2026-08-20T10:42:00Z</span>
        <span class="category">Corporate</span>
        <a class="url" href="https://example.com/tcs-ai">Link</a>
    </div>
</body>
</html>
"""

HTML_VERSION_B = """
<!DOCTYPE html>
<html>
<body>
    <article class="event-card" data-symbol="TCS">
        <div class="event-header">
            <span class="type-tag">Corporate</span>
            <time class="event-time" datetime="2026-08-20T10:42:00Z">10:42 AM</time>
        </div>
        <h2 class="title">New AI investment announced</h2>
        <a class="source-link" href="https://example.com/tcs-ai">Link</a>
    </article>
</body>
</html>
"""

SCHEMA = {
    "symbol": "required",
    "headline": "required",
    "timestamp": "required",
    "category": "optional",
    "url": "required"
}

SELECTORS_A = {
    "row_container": ".market-event",
    "symbol": ".symbol",
    "headline": ".headline",
    "timestamp": ".timestamp",
    "category": ".category",
    "url": "a.url"
}

def test_parse_version_a_success():
    records, excerpt = parse_html_content(HTML_VERSION_A, SELECTORS_A, SCHEMA)
    assert len(records) == 1
    rec = records[0]
    assert rec["symbol"] == "TCS"
    assert rec["headline"] == "New AI investment announced"
    assert rec["timestamp"] == "2026-08-20T10:42:00Z"
    assert rec["category"] == "Corporate"
    assert rec["url"] == "https://example.com/tcs-ai"

def test_parse_version_b_failure_with_selectors_a():
    records, excerpt = parse_html_content(HTML_VERSION_B, SELECTORS_A, SCHEMA)
    # The container .market-event doesn't exist, so no rows should be found
    assert len(records) == 0

def test_health_evaluation():
    # 1. 100% Healthy records
    healthy_records = [{
        "symbol": "TCS",
        "headline": "AI investment",
        "timestamp": "2026-08-20T10:42:00Z",
        "category": "Corporate",
        "url": "https://example.com/tcs-ai"
    }]
    score, status, details = calculate_health_score(healthy_records, SCHEMA)
    assert score == 100.0
    assert status == "HEALTHY"

    # 2. Degraded records: missing required field (headline)
    degraded_records = [{
        "symbol": "TCS",
        "headline": None,
        "timestamp": "2026-08-20T10:42:00Z",
        "category": "Corporate",
        "url": "https://example.com/tcs-ai"
    }]
    score, status, details = calculate_health_score(degraded_records, SCHEMA)
    assert score < 90.0
    assert status == "DEGRADED"
    assert "headline" in details["completely_missing_required"]

def test_healing_proposal_generation():
    # Define last known good state
    history = [{
        "symbol": "TCS",
        "headline": "New AI investment announced",
        "timestamp": "2026-08-20T10:42:00Z",
        "category": "Corporate",
        "url": "https://example.com/tcs-ai"
    }]
    
    proposed_map, explanation = generate_repair_proposal(HTML_VERSION_B, SELECTORS_A, SCHEMA, history)
    
    assert proposed_map is not None
    assert proposed_map["row_container"] == "article.event-card"
    assert proposed_map["symbol"] == "attr:data-symbol"
    assert proposed_map["headline"] == ".title" or proposed_map["headline"] == "h2.title"
    assert proposed_map["url"] == "a.source-link"

def test_diff_selectors():
    old = {"symbol": ".symbol", "headline": ".headline"}
    new = {"symbol": "attr:data-symbol", "headline": ".title"}
    diff = diff_selector_mappings(old, new)
    assert len(diff["CHANGED"]) == 2
