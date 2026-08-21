# Tathya Development & Testing Manual

This guide describes how to run and test the Tathya platform during active development.

---

## 1. Local Setup
Ensure Python 3.12+ and Node.js 18+ are installed.

```bash
# Clone the repository
git clone <repo-url>
cd lucid-hopper

# Create env file
cp backend/.env.example backend/.env
```

---

## 2. Running the Development Servers

```bash
# Start backend portal (runs on http://localhost:8000)
cd backend
python -m uvicorn app.main:app --reload

# Start frontend dashboard (runs on http://localhost:5173)
cd ../frontend
npm run dev
```

---

## 3. Running Automated Tests

We use `pytest` for backend testing.
```bash
# Run unit & E2E self-healing suites
cd backend
python -m pytest tests
```

---

## 4. Troubleshooting
- **Database lock errors:** SQLite may lock during heavy parallel write actions. A clean database will automatically be generated if you delete `tathya.db` in the `backend/` directory.
- **Port conflicts:** If port 8000 or 5173 is occupied, run `uvicorn app.main:app --port <new_port>` or edit `vite.config.ts`.
