# Tathya — Self-Healing Market Intelligence Scraper Platform

**"Evidence before action."** — _Tathya (Sanskrit: तथ्य — fact / truth)_

> Tathya is a production-grade, self-healing web data scraping and market intelligence platform. It uses **Bright Data Scraper Studio** to collect real-time financial news, validates scraped data with an automated health scoring engine, and when website layouts change and break selectors — it automatically generates AI-powered repair proposals, verifies them, and restores pipeline health to 100%.

Built for the [**Scrape-Verse Hackathon**](https://www.wemakedevs.org/events/scrape-verse) by WeMakeDevs × Bright Data.

[![Live Demo](https://img.shields.io/badge/Live-Tathya%20on%20Vercel-000000?style=for-the-badge&logo=vercel)](https://tathya-nhh2s5m7-tvk3.vercel.app)
[![API Health](https://img.shields.io/badge/API-Render%20Backend-22c55e?style=for-the-badge&logo=render)](https://tathya-backend.onrender.com/docs)
[![Bright Data](https://img.shields.io/badge/Powered%20By-Bright%20Data-0ea5e9?style=for-the-badge)](https://brightdata.com)

---

## One-Line Pitch

*Tathya scrapes real-time market news using Bright Data Scraper Studio, detects when website DOM changes break data extraction, auto-generates CSS selector repair proposals, and restores scraper health — all through a live console UI that judges can interact with.*

---

## Live Demo

| Surface | URL |
|---|---|
| **Tathya UI** | [tathya-nhh2s5m7-tvk3.vercel.app](https://tathya-nhh2s5m7-tvk3.vercel.app) |
| **Backend API Docs** | [tathya-backend.onrender.com/docs](https://tathya-backend.onrender.com/docs) |
| **Source Code** | [github.com/trivikramkalagi91-commits/TATHYA](https://github.com/trivikramkalagi91-commits/TATHYA) |

**Login Credentials (for hackathon judges):**
| Field | Value |
|---|---|
| Email | `admin@tathya.io` |
| Password | `tathya_admin_2026` |

---

## 3-Minute Judge Walkthrough

1. Open the [Live Demo](https://tathya-nhh2s5m7-tvk3.vercel.app) → Sign in with the credentials above
2. **Overview** → See live KPI metrics: Active Sources, Healthy Scrapers, Records Collected, Repairs Count
3. **Sources & Scrapers** → Click **Google News Feed** → Click **RUN SCRAPER** → Watch it extract 38+ real-time articles at 100% Health
4. **Self-Healing Logs** → Review repair proposals with side-by-side selector diffs → **Approve & Restore** a pending proposal → Watch live verification progress
5. **Market Intelligence** → See real news in Evidence Breakdown with symbol tagging and trade scenario recommendations
6. **Integrations & Keys** → See the live Bright Data API key integration status
7. Check the sidebar footer → **Bright Data — Connected** indicator with green dot

---

## Screenshots

### Overview Dashboard
![Overview Dashboard — Live KPI metrics, scraper activity timeline, and pipeline health monitor](screenshots/overview-dashboard.png)

### Sources & Scrapers
![Sources & Scrapers — All data pipeline sources with HEALTHY status and 100% health scores](screenshots/sources-scrapers.png)

### Scraper Run Report (Google News — 38 Records, 100% Health)
![Scraper Run Report — Google News Feed extraction with HEALTHY status, CSS selector mapping, and validation schema](screenshots/scraper-run-report.png)

### Self-Healing Logs & Repair Proposals
![Self-Healing Logs — Repair proposals with REPAIRED, PENDING APPROVAL, and FAILED states](screenshots/self-healing-logs.png)

### Project Library (Landing Page)
![Project Library — Choose a scraper target, filter by health status](screenshots/project-library.png)

---

## What Tathya Does

```mermaid
journey
  title Tathya Self-Healing Pipeline Journey
  section Scrape
    Configure data source: 5: User
    Trigger Bright Data Scraper: 5: Tathya
    Collect real-time news: 5: Bright Data
    Parse and normalize records: 5: Tathya
  section Validate
    Health score calculation: 5: Tathya
    Field fill-rate analysis: 5: Tathya
    Detect missing selectors: 5: Tathya
  section Heal
    Generate repair proposal: 5: Tathya
    Side-by-side selector diff: 5: User
    Approve and re-verify: 5: User, Tathya
    Restore pipeline to 100%: 5: Tathya
```

### Features

| Layer | Capability |
|---|---|
| **Scrape** | Bright Data Scraper Studio integration, Google News + Yahoo Finance custom scrapers, real-time cloud data collection, nested JSON unpacking, field normalization |
| **Validate** | Automated health scoring engine, field fill-rate analysis, required/optional schema validation, health status classification (HEALTHY / DEGRADED / FAILED) |
| **Heal** | AI-powered CSS selector repair proposal generation, side-by-side configuration diff, human-in-the-loop approval, live verification runner, automatic pipeline restoration |
| **Observe** | Live market ticker bar, KPI dashboard metrics, alert system (CRITICAL / WARNING / INFO), scraper activity timeline, pipeline health monitor |
| **Intelligence** | Symbol-tagged news timeline, evidence breakdown per stock, AI-generated quant trade scenarios (Entry / Invalidation / Target), multi-source watchlist |

---

## How Bright Data Scraper Studio Is Used

Tathya uses **Bright Data's Scraper Studio** to create and run **two custom web scrapers**:

### 1. Google News Scraper (`c_mt1kxhy7xk57uulqt`)
- **Target:** `https://news.google.com/rss`
- **Custom Parser Code:** Extracts article titles, links, and publish dates from the Google News RSS XML feed
- **Output:** 38+ real-time news articles per run

### 2. Yahoo Finance Scraper (`c_mt1jr7ct6tl8herk2`)
- **Target:** `https://finance.yahoo.com/news/`
- **Custom Parser Code:** Uses structural CSS selectors (`h3`, `a`, `time`) to extract headlines, URLs, timestamps, and publisher sources from Yahoo's live news feed
- **Output:** 20+ real-time financial news articles per run

### Integration Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant BD as Bright Data API
    participant DB as Supabase PostgreSQL

    U->>FE: Click "RUN SCRAPER"
    FE->>BE: POST /api/v1/collectors/{id}/run
    BE->>BD: POST /dca/trigger (collector_id, url)
    BD-->>BE: {collection_id: "j_xxx"}
    loop Poll every 3s (max 60s)
        BE->>BD: GET /dca/dataset?id=j_xxx
        BD-->>BE: 202 (still running) or 200 (data ready)
    end
    BD-->>BE: 200 [{articles: [...]}]
    BE->>BE: Unpack nested JSON, normalize fields
    BE->>BE: Calculate health score (field fill-rate)
    BE->>DB: Save ScrapeRun, ScrapeRecords, HealthCheck
    BE-->>FE: {records: 38, health: 100%, status: HEALTHY}
    FE-->>U: Display green HEALTHY badge + records table
```

---

## Example Structured Output from Scraper Studio

### Google News Scraper Output (38 records)
```json
[
  {
    "symbol": null,
    "headline": "Elon Musk Is No Longer a Trillionaire After Tesla Stock Plunge",
    "timestamp": "2026-08-22T10:09:58.517Z",
    "category": "Business",
    "url": "https://news.google.com/articles/CBMiWkFVX3lxTE..."
  },
  {
    "symbol": "AAPL",
    "headline": "Apple declares record quarterly dividend as iPhone sales surge",
    "timestamp": "2026-08-22T09:42:00.000Z",
    "category": "Corporate",
    "url": "https://news.google.com/search?q=Apple+declares+record..."
  }
]
```

### Yahoo Finance Scraper Output (20 records)
```json
[
  {
    "symbol": null,
    "headline": "If a Stock Market Crash Is Coming, These 3 Stocks Could Benefit",
    "timestamp": "2026-08-22T10:54:886Z",
    "category": "Yahoo Finance",
    "url": "https://finance.yahoo.com/news/stock-market-crash-coming..."
  },
  {
    "symbol": null,
    "headline": "Warren Buffett's Last Warning to Investors Before 2027",
    "timestamp": "2026-08-22T10:54:861Z",
    "category": "Yahoo Finance",
    "url": "https://finance.yahoo.com/news/warren-buffetts-last-warning..."
  }
]
```

---

## System Architecture

```mermaid
flowchart TB
  subgraph Client["Frontend — React + TypeScript + Vite"]
    UI[Dashboard + Console UI]
  end

  subgraph API["Backend — FastAPI + Python"]
    R[API Router /api/v1]
    SC[Scraper Engine]
    HE[Health Engine]
    SH[Self-Healing Engine]
  end

  subgraph Data["Database"]
    PG[(Supabase PostgreSQL)]
  end

  subgraph Ext["External Services"]
    BD[Bright Data Scraper API]
    FH[Finnhub Stock API]
  end

  subgraph Deploy["Hosting"]
    V[Vercel - Frontend]
    RN[Render - Backend]
  end

  UI -->|REST API| R
  R --> SC
  R --> HE
  R --> SH
  SC -->|Trigger + Poll| BD
  SC -->|Local Fallback| SC
  HE -->|Field Validation| PG
  SH -->|Repair Proposals| PG
  R -->|Live Prices| FH
  UI -.-> V
  R -.-> RN
  R --> PG
```

---

## Self-Healing Pipeline (Core Innovation)

```mermaid
flowchart LR
  RUN[Run Scraper] --> HEALTH{Health Score?}
  HEALTH -->|100%| HEALTHY[✅ HEALTHY<br/>Records saved]
  HEALTH -->|< 100%| DETECT[⚠️ Degradation Detected]
  DETECT --> ANALYZE[Analyze broken HTML DOM]
  ANALYZE --> PROPOSE[Generate Repair Proposal<br/>New CSS selectors]
  PROPOSE --> DIFF[Show side-by-side diff<br/>Old vs Proposed selectors]
  DIFF --> APPROVE{Judge Approves?}
  APPROVE -->|Yes| VERIFY[Re-run scraper with<br/>new selectors]
  VERIFY --> RESTORED[✅ REPAIRED<br/>Pipeline restored to 100%]
  APPROVE -->|No| REJECT[❌ Proposal rejected]
```

| Step | What Happens |
|---|---|
| **Detect** | Health engine calculates field fill-rates against required schema. If any required field (headline, url, timestamp) drops below threshold → DEGRADED/FAILED |
| **Analyze** | Backend fetches raw HTML from the target site, analyzes DOM structure for structural elements matching the expected data pattern |
| **Propose** | Generates new CSS selector mappings (e.g., `div.substream` → `section.substream`, `h3` → `h2.title`) |
| **Review** | User sees a side-by-side diff: "DEGRADED CONFIG (VERSION A)" vs "REPAIRED CONFIG (PROPOSAL)" |
| **Verify** | After approval, re-runs the scraper with updated selectors and validates health returns to 100% |
| **Restore** | Updates collector database with new selectors, marks repair as REPAIRED, triggers recovery alert |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Axios |
| **Backend** | FastAPI, Python 3.13, Pydantic, SQLAlchemy, Uvicorn, BeautifulSoup4 |
| **Database** | Supabase (PostgreSQL), SQLite (local dev) |
| **Scraping** | Bright Data Scraper Studio (Data Collector API), Custom Cheerio parsers |
| **Market Data** | Finnhub Stock API (live prices, exchange rates) |
| **Frontend Hosting** | Vercel |
| **Backend Hosting** | Render |

---

## Setup & Local Development

### 1. Clone the Repository
```bash
git clone https://github.com/trivikramkalagi91-commits/TATHYA.git
cd TATHYA
```

### 2. Configure Backend Environment
Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL=sqlite:///./tathya.db
BRIGHT_DATA_API_TOKEN=your_bright_data_api_token
MARKET_NEWS_API_KEY=your_finnhub_api_key
JWT_SECRET=your_jwt_secret
ENV=development
```

### 3. Run Backend Server
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Run Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to access the Tathya console.

**Default Admin Credentials:**
| Field | Value |
|---|---|
| Email | `admin@tathya.io` |
| Password | `tathya_admin_2026` |

---

## Test Execution

Run the automated unit and E2E self-healing validation test suite:
```bash
cd backend
python -m pytest tests
```

```
===== 6 passed, 0 failed =====
```

---

## Project Structure

```
TATHYA/
├── backend/
│   ├── app/
│   │   ├── config.py              # Settings, env vars, Bright Data keys
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── db/session.py          # SQLAlchemy database session
│   │   ├── models/models.py       # ORM models (User, Source, Collector, ScrapeRun, Repair, etc.)
│   │   ├── schemas/schemas.py     # Pydantic request/response schemas
│   │   ├── routes/
│   │   │   ├── auth.py            # JWT authentication
│   │   │   ├── collectors.py      # Scraper trigger, health scoring, self-healing
│   │   │   ├── repairs.py         # Repair proposal approval and verification
│   │   │   ├── health.py          # Dashboard KPI metrics aggregation
│   │   │   ├── market.py          # Market events, watchlist, trade scenarios
│   │   │   └── alerts.py          # Alert system
│   │   ├── integrations/
│   │   │   └── brightdata.py      # Bright Data DCA API trigger + poll
│   │   └── services/
│   │       ├── scraper.py         # BeautifulSoup local scraper engine
│   │       ├── health_calculator.py  # Field fill-rate health scoring
│   │       └── self_healer.py     # CSS selector repair proposal generator
│   ├── tests/
│   │   ├── test_e2e.py            # End-to-end self-healing workflow test
│   │   └── test_scraper.py        # Scraper unit tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # Complete React SPA (dashboard, console, scrapers)
│   │   ├── lib/api.ts             # Axios API client
│   │   └── main.tsx               # Vite entry point
│   ├── index.html
│   └── package.json
└── README.md
```

---

## AI Disclosure

This project was built during the Scrape-Verse hackathon (August 17–23, 2026). AI coding assistants (Antigravity by Google DeepMind) were used for pair programming, debugging, and code generation. All code was reviewed, understood, and verified by the developer. The project architecture, design decisions, and Bright Data scraper configurations were directed by the developer.

---

## License

MIT License — Built with ❤️ for the Scrape-Verse Hackathon by WeMakeDevs × Bright Data.
