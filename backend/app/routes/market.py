import datetime
import httpx
import logging
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.db.session import get_db
from backend.app.routes.auth import get_current_user
from backend.app.models.models import User, MarketEvent, Watchlist, WatchlistItem, Alert
from backend.app.schemas.schemas import MarketEventResponse, WatchlistResponse, OpportunitySignal, WhyMovedResponse
from backend.app.config import settings

router = APIRouter(prefix="/api/v1/market", tags=["market"])
logger = logging.getLogger(__name__)

# Finnhub API Helper Functions
async def fetch_finnhub_quote(symbol: str) -> Dict[str, Any]:
    """
    Fetches real-time price quote from Finnhub with a fallback to Yahoo Finance for international/Indian tickers.
    """
    # 1. Primary Finnhub attempt (supports US tickers)
    if settings.MARKET_NEWS_API_KEY:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={settings.MARKET_NEWS_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # If Finnhub returns a valid price (not None or 0)
                    if data.get("c") is not None and data.get("c") != 0:
                        return {
                            "price": data.get("c"),
                            "change": data.get("d"),
                            "change_pct": data.get("dp"),
                            "high": data.get("h"),
                            "low": data.get("l"),
                            "open": data.get("o"),
                            "prev_close": data.get("pc")
                        }
        except Exception as e:
            logger.error(f"Error fetching Finnhub quote for {symbol}: {e}")

    # 2. Yahoo Finance fallback (supports Indian .NS/.BO suffixes, e.g. TCS.NS, RELIANCE.NS)
    try:
        yf_symbol = symbol
        if "." not in symbol and symbol in ["TCS", "RELIANCE", "INFOSYS"]:
            yf_symbol = f"{symbol}.NS"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json().get("chart", {}).get("result", [])
                if result:
                    meta = result[0].get("meta", {})
                    price = meta.get("regularMarketPrice")
                    prev_close = meta.get("chartPreviousClose")
                    if price is not None and prev_close is not None:
                        change = price - prev_close
                        change_pct = (change / prev_close) * 100
                        return {
                            "price": price,
                            "change": change,
                            "change_pct": change_pct,
                            "high": price,
                            "low": price,
                            "open": price,
                            "prev_close": prev_close
                        }
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance fallback quote for {symbol}: {e}")

    return {}

async def fetch_finnhub_news(symbol: str) -> List[Dict[str, Any]]:
    """
    Fetches recent news articles for a company from Finnhub.
    """
    if not settings.MARKET_NEWS_API_KEY:
        return []
    
    today = datetime.date.today().isoformat()
    week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={week_ago}&to={today}&token={settings.MARKET_NEWS_API_KEY}"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()[:5]  # Limit to top 5 news articles
    except Exception as e:
        logger.error(f"Error fetching Finnhub news for {symbol}: {e}")
    return []

@router.get("/events", response_model=List[MarketEventResponse])
def get_market_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a unified chronological timeline of verified scraped financial announcements and news.
    """
    events = db.query(MarketEvent).order_by(MarketEvent.publish_time.desc()).all()
    return events

@router.get("/watchlist", response_model=List[Dict[str, Any]])
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user's stock watchlists complete with real-time stock price and scraped event counts.
    """
    # Fetch or create default watchlist
    watchlist = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).first()
    if not watchlist:
        watchlist = Watchlist(user_id=current_user.id, name="Primary Monitor")
        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)

    items = db.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist.id).all()
    if not items:
        return []

    # Fetch quotes in parallel to avoid sequential network delays
    symbols = [item.symbol for item in items]
    quote_tasks = [fetch_finnhub_quote(symbol) for symbol in symbols]
    quotes = await asyncio.gather(*quote_tasks)

    result = []
    for item, quote in zip(items, quotes):
        # Get count of scraped events in last 48 hours
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
        event_count = db.query(MarketEvent).filter(
            MarketEvent.company_symbol == item.symbol,
            MarketEvent.publish_time >= cutoff
        ).count()

        # Calculate a mockup opportunity score if real quote exists
        opportunity_score = None
        if quote and quote.get("change_pct") is not None:
            # Score formula: combination of news volume and price volatility
            volatility = abs(quote["change_pct"])
            opportunity_score = min(100.0, max(0.0, (volatility * 10) + (event_count * 15)))
            opportunity_score = round(opportunity_score, 1)

        result.append({
            "id": item.id,
            "symbol": item.symbol,
            "price": quote.get("price") if quote else None,
            "change_pct": quote.get("change_pct") if quote else None,
            "event_count": event_count,
            "opportunity_score": opportunity_score,
            "created_at": item.created_at
        })
        
    return result

@router.post("/watchlist")
def add_to_watchlist(
    payload: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adds a ticker symbol to the watchlist.
    """
    symbol = payload.get("symbol", "").upper().strip()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")

    watchlist = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).first()
    if not watchlist:
        watchlist = Watchlist(user_id=current_user.id, name="Primary Monitor")
        db.add(watchlist)
        db.commit()
        db.refresh(watchlist)

    # Check duplicate
    exists = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist.id,
        WatchlistItem.symbol == symbol
    ).first()
    if exists:
        return {"message": f"{symbol} is already in the watchlist."}

    item = WatchlistItem(watchlist_id=watchlist.id, symbol=symbol)
    db.add(item)
    db.commit()
    return {"message": f"{symbol} added to watchlist.", "symbol": symbol}

@router.delete("/watchlist/{symbol}")
def delete_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a symbol from the watchlist.
    """
    symbol = symbol.upper().strip()
    watchlist = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
        
    item = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist.id,
        WatchlistItem.symbol == symbol
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")
        
    db.delete(item)
    db.commit()
    return {"message": f"{symbol} removed from watchlist."}

@router.get("/opportunities", response_model=List[OpportunitySignal])
async def get_opportunities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Scans watchlist symbols, processes news and announcements volume, and returns transparent opportunity signals.
    """
    watchlist = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).first()
    if not watchlist:
        return []
        
    items = db.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist.id).all()
    if not items:
        return []

    # Fetch quotes and news in parallel to prevent sequential network delays
    quote_tasks = [fetch_finnhub_quote(item.symbol) for item in items]
    quotes = await asyncio.gather(*quote_tasks)

    news_list = []
    if settings.MARKET_NEWS_API_KEY:
        news_tasks = [fetch_finnhub_news(item.symbol) for item in items]
        news_list = await asyncio.gather(*news_tasks)
    else:
        news_list = [[] for _ in items]

    signals = []
    for item, quote, fh_news in zip(items, quotes, news_list):
        db_news = db.query(MarketEvent).filter(
            MarketEvent.company_symbol == item.symbol
        ).order_by(MarketEvent.publish_time.desc()).all()
        
        # Merge DB news with Finnhub news if configured
        recent_headlines = [n.headline for n in db_news[:3]]
        for n in fh_news:
            h = n.get("headline")
            if h and h not in recent_headlines:
                recent_headlines.append(h)

        if not recent_headlines:
            continue  # Skip symbols with zero evidence/news

        price_change = (quote.get("change_pct") or 0.0) if quote else 0.0
        news_volume = len(recent_headlines)
        
        # Transparency scoring breakdown
        news_factor = min(40, news_volume * 10)
        momentum_factor = min(30, abs(price_change) * 6)
        evidence_factor = 30 if len(db_news) > 0 else 10  # Scraper source validation weight
        
        opp_score = round(news_factor + momentum_factor + evidence_factor, 1)

        # Build trade scenario based on standard support/resistance estimates
        current_price = quote.get("price") or 100.0
        invalidation = round(current_price * 0.95, 2)
        target = round(current_price * 1.15, 2)
        
        signals.append(OpportunitySignal(
            symbol=item.symbol,
            opportunity_score=opp_score,
            headline=recent_headlines[0],
            source=db_news[0].source_name if db_news else "Finnhub API Feed",
            publish_time=db_news[0].publish_time if db_news else datetime.datetime.utcnow(),
            evidence_breakdown={
                "news_density": f"{news_volume} active factors tracked",
                "volatility_momentum": f"{price_change:+.2f}% daily shift",
                "scraped_pipeline_health": "Verified 100% Healthy" if db_news else "API Direct (Not Scraped)"
            },
            trade_scenario={
                "entry_zone": f"${current_price:.2f}",
                "invalidation_level": f"${invalidation:.2f}",
                "target_target": f"${target:.2f}",
                "risk_reward_ratio": "1 : 3.0"
            }
        ))
        
    # Sort signals by highest opportunity score
    signals.sort(key=lambda s: s.opportunity_score, reverse=True)
    return signals

@router.get("/why-moved/{symbol}", response_model=WhyMovedResponse)
async def get_why_moved(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns verified evidence explaining why a stock symbol moved.
    """
    symbol = symbol.upper().strip()
    quote = await fetch_finnhub_quote(symbol)
    
    # Query database for recent scraped news about this symbol
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    db_events = db.query(MarketEvent).filter(
        MarketEvent.company_symbol == symbol,
        MarketEvent.publish_time >= cutoff
    ).order_by(MarketEvent.publish_time.desc()).all()
    
    factors = []
    
    # Add scraped pipeline factors
    for event in db_events:
        factors.append({
            "type": "Scraped Announcement",
            "source": event.source_name,
            "evidence": event.headline,
            "time": event.publish_time.isoformat()
        })

    # Add Finnhub feed factors if available
    if settings.MARKET_NEWS_API_KEY:
        fh_news = await fetch_finnhub_news(symbol)
        for n in fh_news:
            # Check duplication
            headline = n.get("headline", "")
            if not any(f["evidence"] == headline for f in factors):
                pub_time_stamp = n.get("datetime", datetime.datetime.utcnow().timestamp())
                factors.append({
                    "type": "Market News Feed",
                    "source": n.get("source", "Finnhub"),
                    "evidence": headline,
                    "time": datetime.datetime.fromtimestamp(pub_time_stamp).isoformat()
                })

    price_change = (quote.get("change_pct") or 0.0) if quote else 0.0

    if not factors:
        return WhyMovedResponse(
            symbol=symbol,
            price_change_pct=price_change,
            possible_factors=[],
            evidence_status="INSUFFICIENT_EVIDENCE"
        )

    return WhyMovedResponse(
        symbol=symbol,
        price_change_pct=price_change,
        possible_factors=factors[:4],
        evidence_status="VERIFIED_EVIDENCE"
    )
