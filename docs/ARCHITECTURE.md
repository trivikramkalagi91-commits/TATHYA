# Tathya Architecture Guide

This document describes the architectural layout, data flow, and components of the Tathya platform.

---

## 1. System Components Layout

```
                  +-----------------------------------------+
                  |            REACT / VITE UI              |
                  |  (Overview, Scrapers, Healing, Market)  |
                  +--------------------|--------------------+
                                       | HTTPS REST JSON
                                       v
                  +-----------------------------------------+
                  |             FASTAPI PORTAL              |
                  |     (Routers, Middleware, CORS)         |
                  +---|-----------------|---------------|---+
                      |                 |               |
                      v                 v               v
             +----------+         +-----------+   +-----------+
             | DATABASE |         |  SCRAPER  |   | HEALING & |
             | (SQLite) |         |  ENGINE   |   |  HEALTH   |
             +----------+         +-----+-----+   +-----+-----+
                                        |               |
                       +----------------+               |
                       |                                |
                       v                                v
     +-----------------+-------------------+      +-----+-----+
     |             INTERNET                |      |  PROPOSAL |
     | (Bright Data DCA / Finnhub Quotes)  |      | GENERATOR |
     +-------------------------------------+      +-----------+
```

---

## 2. Relational Database Schema

We use SQLAlchemy schemas. The entity mapping relationships are structured as:

- **`User`** -> Has many **`Workspace`**
- **`Workspace`** -> Has many **`Project`**
- **`Project`** -> Has many **`Source`**
- **`Source`** -> Has many **`Collector`** and **`Repair`**
- **`Collector`** -> Has many **`ScrapeRun`**, **`HealthCheck`**, and **`Repair`**
- **`ScrapeRun`** -> Has many **`ScrapeRecord`** and one **`HealthCheck`**
- **`MarketEvent`** -> Stores verified, normalized scraped market items for watchlists.
- **`Watchlist`** -> Has many **`WatchlistItem`** linked to monitored symbols.
- **`Alert`** -> Stores pipeline warning and recovery flags.

---

## 3. Data Scrape & Heal Lifecycle

1. **Scraper Execution:** Scraper fetches the target page HTML directly or via the Bright Data Collector API.
2. **Quality Check:** The health engine parses attributes, checks against required fields schema, and determines a health score.
3. **Degradation Detection:** If health drops beneath 90%, it locks publication downstream, alerts the workspace, and logs a repair.
4. **Heuristic Alignment:** The healing service extracts the last known healthy records from the database and searches the new HTML structure to locate where these texts went, generating repaired selectors.
5. **Human Approval:** The user reviews the before/after selector diff and clicks "Approve."
6. **E2E Verification:** Tathya updates the parser selectors, runs a verification check, verifies that health returns to 100%, and publishes verified market events.
