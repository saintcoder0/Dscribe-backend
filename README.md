# Patient Admission Management — Backend

FastAPI + Pydantic REST API backed by MongoDB Atlas (`pymongo`) for managing hospital patient admissions.

## Live Links

- **Backend API:** https://dscribe-backend.vercel.app
- **API Docs (Swagger):** https://dscribe-backend.vercel.app/docs
- **Frontend:** https://hostpitaladministration.vercel.app

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic, Uvicorn
- **Database:** MongoDB Atlas (`pymongo` sync driver)
- **Package Manager:** `uv` (with `requirements.txt` also provided for `pip`-based hosts)
- **Frontend (separate repo):** React + Vite ([Dscribe-frontend](https://github.com/saintcoder0/Dscribe-frontend))

## Features

- Startup MongoDB Atlas `ping` check with clear error reporting if `MONGO_URI` is missing or unreachable
- Single source of truth for Gender, Ward, Department, and Doctor option lists (`GET /api/options`)
- Strict Pydantic validation with custom HTTP `422` per-field error responses (`{ "errors": { ... } }`), including IST-based future date checks
- Safe name search (`re.escape()` + case-insensitive `$regex`) combinable with Ward, Department, and Doctor filters
- Converts MongoDB `_id` to string `id` and returns `404` on invalid ObjectIds or missing records
- Environment-configurable CORS origins

## Project Structure

```text
backend/
├── main.py            # FastAPI app, routes, CORS, 422 validation handler
├── database.py        # MongoClient, patients collection, startup ping
├── schemas.py         # Pydantic models, validation rules, option lists
├── pyproject.toml     # uv project configuration
├── uv.lock            # Locked dependency versions
├── requirements.txt   # pip-compatible dependencies
├── .env.example       # Environment variable placeholders
├── .gitignore
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your values (never commit `.env`):

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB Atlas connection string | `mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority` |
| `DB_NAME` | MongoDB database name | `hospital` |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |

## Steps to Run Locally

### 1. MongoDB Atlas Setup

1. Create a free **M0** cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).
2. Under **Database Access**, create a database user and password.
3. Under **Network Access**, allow IP `0.0.0.0/0` (needed for cloud deployments).
4. Under **Connect → Drivers → Python**, copy your `mongodb+srv://...` connection string.

### 2. Run with `uv` (Recommended)

```bash
uv sync
cp .env.example .env
# Edit .env and set MONGO_URI, DB_NAME, and CORS_ORIGINS
uv run uvicorn main:app --reload
```

### Alternative: Run with `venv` + `pip`

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

The API runs at `http://localhost:8000` and interactive docs are at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/options` | Returns allowed genders, wards, departments, and doctors |
| `GET` | `/api/patients` | List patients (optional `search`, `ward`, `department`, `doctor` query params) |
| `POST` | `/api/patients` | Create a new patient admission (`status` defaults to `Admitted`) → `201` |
| `PUT` | `/api/patients/{id}` | Update an existing patient record |
| `PATCH` | `/api/patients/{id}/discharge` | Mark a patient as `Discharged` |
| `DELETE` | `/api/patients/{id}` | Delete a patient record → `204` |
| `GET` | `/health` | Health check (`{"status": "ok"}`) |
