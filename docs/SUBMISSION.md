# Tathya Hackathon Submission Summary

Tathya is a self-healing web data scraping and intelligence platform designed to keep critical web pipelines alive even when websites change.

---

## What We Built

1. **A Modular FastAPI Backend:** Features a custom secure PBKDF2-HMAC-SHA256 password-hashing authentication system, SQLAlchemy models, and structured SQLite logging.
2. **A Controlled Demo Target:** An internal website serving Version A (standard CSS classes) and Version B (semantic tags and data attributes) with a dashboard toggle control.
3. **A Scraper Health & Heuristic Engine:** Calculates extraction fill-rates (weighting required vs. optional fields) and flags DOM selector changes.
4. **An Auto-Healing Alignment Engine:** Automatically locates historical news headlines, symbols, and links in mutated pages to generate corrected CSS selectors without cloud dependencies.
5. **A Premium Financial UI:** A charcoal-dark Bloomberg/Linear-style dashboard with a step-by-step selector diff visualizer, verified chronological timelines, watchlist, and opportunities scanner.
6. **A Full E2E Test Suite:** Validates that when Version B breaks the scraper, a repair proposal is generated and, once approved, restores pipeline health to 100%.
7. **Bright Data & Finnhub Integrations:** Features a wrapper for triggering Web Scrapers and polling datasets, plus live stock pricing updates.
