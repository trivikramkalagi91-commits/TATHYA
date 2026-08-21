# Tathya — "Evidence before action."

Tathya (Sanskrit: तथ्य — fact / truth) is a production-grade, self-healing web data scraping and intelligence platform designed to keep critical web pipelines alive even when websites change. 

Websites deploy changes constantly. Standard scrapers break, resulting in silent missing fields, stale records, and corrupt downstream metrics. Tathya monitors scraper datasets, flags layout degradation, deduces updated CSS selectors using a structural heuristic engine, prompts human validation, and updates scraper models to restore pipeline health to 100%.

---

## Technical Stack & Architecture

- **Backend:** FastAPI, Pydantic, SQLAlchemy, Uvicorn, BeautifulSoup4.
- **Frontend:** React, Vite, TypeScript, Axios, Lucide-React.
- **Database:** SQLite (zero-config local evaluation), fully compatible with PostgreSQL.
- **APIs & Integrations:** 
  - **Bright Data DCA (Data Collector API):** Real-time web scraper pipeline execution.
  - **Finnhub Stock API:** Live stock pricing feeds and market announcements.

---

## Setup & Startup Instructions

### 1. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
DATABASE_URL=sqlite:///./tathya.db
BRIGHT_DATA_API_TOKEN=c22b9a59-2110-465e-9deb-586f3a2a43d6
MARKET_NEWS_API_KEY=da3fpv9r01qual4puom0da3fpv9r01qual4puomg
ENV=development
```

### 2. Run Backend Server
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Upon startup, the backend automatically initializes database tables and seeds a default administrative user:
- **Email:** `admin@tathya.io`
- **Password:** `tathya_admin_2026`

### 3. Run Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to explore the Tathya interface.

---

## Live Demo Scenario (How to Test Breakage & Self-Healing)

1. Sign in to the dashboard at `http://localhost:5173/#login` using:
   - **Email:** `admin@tathya.io` | **Password:** `tathya_admin_2026`
2. Go to **Sources & Scrapers** -> Click **"Tathya Controlled Feed"**.
3. Under the selector preview tab, notice the scraper is using standard CSS selectors (`.market-event`, `.headline`, `.timestamp`, `.symbol`, `a.url`).
4. Click **Run Scraper**. It executes against Version A of our internal site. The run completes with **100% Health** and extracts 5 news announcements.
5. In the controlled layout control panel, click **"Version B (Changed DOM)"**. This dynamically alters the server's target HTML DOM structure, mimicking a real site update.
6. Click **Run Scraper** again. The scrape executes and immediately fails with **0% Health**.
7. Scroll down to review the warning. Tathya has detected that the required fields (`headline`, `timestamp`, `symbol`, `url`) are completely missing, and has filed a **Repair Proposal**.
8. Click **Review Repair Proposal** (or go to the **Self-Healing Logs** tab).
9. You will see a side-by-side diff comparing the broken selectors (classes) with the proposed fixes (`article.event-card`, `attr:data-symbol`, `.title`, `time`).
10. Click **Approve & Restore Data Pipeline**. A loader will simulate verification checks while backend runs are executed against Version B using the proposed selectors.
11. The repair logs complete as **REPAIRED**.
12. Go back to **Market Intelligence**. You will see that the verified news timelines and trade scenarios have fully recovered and are updating again.

---

## Test Execution
Run the automated unit and E2E self-healing validation test suite:
```bash
cd backend
python -m pytest tests
```

---

## AI Disclosure
Password hashing algorithms, selector alignment structures, and database models were built by Antigravity, an AI assistant, following clean code pair-programming guidelines.
