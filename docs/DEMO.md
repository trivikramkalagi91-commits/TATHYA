# Tathya Hackathon Demonstration Guide

This guide outlines the step-by-step presentation script to demonstrate Tathya's core capabilities in 3 minutes.

---

## The Presentation Narrative

> **"Web pages change constantly. Scrapers break. Tathya notices the break, repairs the selectors, verifies the dataset, and keeps downstream market intelligence running."**

---

## Step-by-Step Demo Sequence

### 1. Show a Healthy Pipeline
- Log in to the console (`admin@tathya.io` / `tathya_admin_2026`).
- Go to **Sources & Scrapers**.
- Select the **"Tathya Controlled Feed"** (running on Version A).
- Click **Run Scraper**.
- **Observation:** Scraper run completes with **100% Health**, extracting 5 structured news announcements.
- Go to **Market Intelligence** and show the ticker watchlist updating with news counts.

### 2. Break the Website DOM
- Go back to **Sources & Scrapers**.
- Under the controlled target site panel, toggle to **"Version B (Changed DOM)"**.
- Click **Run Scraper**.
- **Observation:** The scraper immediately fails with **0% Health**.
- Scroll to review the report: required fields (`headline`, `timestamp`, `symbol`, `url`) are missing because the selectors failed to find matching elements in Version B's new layout.

### 3. Review the Repair Proposal
- Go to **Self-Healing Logs** (or click the CTA in the scraper output).
- Review the generated proposal for **Repair #1**.
- Point out the selector comparison:
  - **Old Selector:** `.market-event` | **Proposed Selector:** `article.event-card`
  - **Old Selector:** `.headline` | **Proposed Selector:** `.title`
  - **Old Selector:** `.symbol` | **Proposed Selector:** `attr:data-symbol`
  - **Old Selector:** `.timestamp` | **Proposed Selector:** `time`
- Highlight the **Heuristic Logs** describing how Tathya searched the new HTML tree to align historical headlines and tickers with new tags.

### 4. Approve & Verify
- Click **Approve & Restore Data Pipeline**.
- Observe the real-time backend verification console logs executing:
  - updating db mapping...
  - running verification scrape...
  - validating data fields...
- The state updates to **REPAIRED** with **100% Health**.

### 5. Confirm Recovery
- Go back to **Market Intelligence** and show that downstream timelines and trade scenarios are updating cleanly again, proving that the intelligence pipeline never stayed blind.
