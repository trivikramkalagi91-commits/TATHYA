# Tathya API Specifications

The Tathya FastAPI portal exposes versioned, RESTful endpoints.

---

## 1. Authentication
- `POST /api/v1/auth/signup`: Registers a new user and provisions default workspaces.
- `POST /api/v1/auth/login`: Authenticates credentials and returns a signed JWT.
- `GET /api/v1/auth/me`: Returns the logged-in user profile details.

---

## 2. Sources & Collectors
- `GET /api/v1/sources/`: Lists all registered data sources.
- `POST /api/v1/sources/`: Registers a new source.
- `DELETE /api/v1/sources/{id}`: Removes a source.
- `GET /api/v1/collectors/`: Lists all active scrapers/collectors.
- `POST /api/v1/collectors/{id}/run`: Triggers the scraper parser, evaluates health, and logs results.

---

## 3. Self-Healing & Health
- `GET /api/v1/health/metrics`: Retrieves dashboard aggregation values.
- `GET /api/v1/health/history`: Returns the scraper activity run logs.
- `GET /api/v1/repairs/`: Lists pending selector proposals and history.
- `POST /api/v1/repairs/{id}/approve`: Approves a selector plan, updates selectors, and runs E2E verification.

---

## 4. Market Intelligence
- `GET /api/v1/market/events`: Unified timeline of verified news announcements.
- `GET /api/v1/market/watchlist`: Returns watchlist items with pricing.
- `POST /api/v1/market/watchlist`: Adds a symbol to the tracking watchlist.
- `GET /api/v1/market/opportunities`: Returns opportunity scores and scenarios.
- `GET /api/v1/market/why-moved/{symbol}`: Returns news evidence explaining price shifts.

---

## 5. System Alerts
- `GET /api/v1/alerts/`: Lists all warnings and restoration flags.
- `POST /api/v1/alerts/{id}/read`: Marks an alert as read.
