# Tathya Security Guide

Tathya is designed for enterprise integration, keeping security at its foundation.

---

## 1. Environment Secrets Management
- All API tokens and credentials are kept strictly server-side:
  - `BRIGHT_DATA_API_TOKEN` is loaded into the FastAPI server session.
  - `MARKET_NEWS_API_KEY` (Finnhub) is handled by backend services to query stock parameters.
- Secrets are never transmitted to the frontend or embedded in client-side HTML/JS bundles.
- A `.env.example` file is provided, and `.env` is gitignored.

---

## 2. Authentication & Session Handling
- **Hashing:** Passwords are hashed using the industry-standard **PBKDF2-HMAC-SHA256** algorithm with 100,000 iterations and unique random salts, protecting against database compromise.
- **JWT Authorization:** Authenticated users receive a JWT signed with `HS256` using the backend `JWT_SECRET`. Tokens expire after 24 hours.
- **Protected Routes:** All `/api/v1/` admin endpoints require a valid `Authorization: Bearer <JWT_TOKEN>` header.

---

## 3. Data Provenance & Safety
- Extracted records maintain a strict schema footprint referencing the original scraping run, collection timestamp, and raw source URL.
- Downstream market intelligence models never claim causality or guaranteed profits. Trade scenario panels explicitly warn users of drawdown risk.
- Input fields undergo validation using **Pydantic** schemas to block SQL injection and malformed parameters.
