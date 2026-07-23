# InstaGuard — Forensic Steganography Detection Platform

> Automated detection of covert communications hidden in Instagram images, built for law enforcement and intelligence agencies.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + Tailwind)                               │
│  Login / Register → Dashboard → Scan Detail → Export PDF        │
└───────────────────┬─────────────────────────────────────────────┘
                    │  REST API  (JWT Bearer)
┌───────────────────▼─────────────────────────────────────────────┐
│  FastAPI Backend                                                 │
│  /api/auth  /api/scans  /api/utils/test-cookie                  │
└───────┬─────────────────────────────────┬────────────────────────┘
        │ enqueue task                    │ PostgreSQL (SQLAlchemy)
┌───────▼──────────┐              ┌───────▼───────────────────────┐
│  Celery Worker   │              │  DB Tables                     │
│  Redis broker    │              │  users / scans / post_results  │
│                  │              └───────────────────────────────┘
│  1. Scrape ──────┼──▶  Apify Instagram Scraper
│  2. Fetch bytes  │        directUrls + sessionid cookie
│  3. Detect ──────┼──▶  SRNet Noise Extractor
│  4. Persist      │     + EfficientNet-B2 Classifier
└──────────────────┘
        ↑
   RAM-Only Protocol — clean images are never saved to disk
```

---

## Detection Engine

The model uses a two-stage hybrid neural network:

| Stage | Component | Role |
|-------|-----------|------|
| 1 | **SRNet Noise Extractor** | Strips image content, isolates high-frequency noise residuals where steganographic payloads reside |
| 2 | **EfficientNet-B2 Classifier** | Processes noise feature maps and classifies as `clean` or `stego` with confidence score |

---

## Project Structure

```
instaguard/
├── backend/
│   ├── api/
│   │   ├── auth_router.py       # Register, Login, Google OAuth
│   │   ├── scan_router.py       # Start scan, list, detail, delete, export PDF
│   │   ├── utils_router.py      # /test-cookie (no Apify credit used)
│   │   └── schemas.py           # Pydantic request/response models
│   ├── core/
│   │   └── detector.py          # SRNet + EfficientNet-B2 inference engine
│   ├── models/
│   │   ├── user.py              # SQLAlchemy User model
│   │   ├── scan.py              # Scan + ScanStatus enum
│   │   └── post_result.py       # Per-image detection result
│   ├── tasks/
│   │   └── scan_task.py         # Celery task: scrape → analyze → persist
│   ├── utils/
│   │   ├── auth.py              # JWT helpers, password hashing
│   │   ├── logger.py            # Loguru setup
│   │   └── scraper.py           # ApifyScraper adapter (ported from Flask app)
│   ├── app.py                   # FastAPI app entrypoint
│   ├── config.py                # Pydantic settings
│   ├── database.py              # SQLAlchemy engine + session
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ShieldLogo.jsx
│   │   │   ├── StatCard.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   ├── PostResultCard.jsx
│   │   │   └── ScanHistoryRow.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── hooks/
│   │   │   └── useScans.js      # React Query hooks with auto-polling
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   └── ScanDetailPage.jsx
│   │   ├── utils/
│   │   │   └── api.js           # Axios instance with JWT interceptor
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── data/
│   └── instaguard_model.pth     # ← place your trained model here
├── logs/
└── docker-compose.yml
```

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Apify account + API token → https://console.apify.com/account/integrations
- Instagram `sessionid` cookie (see below)
- Your trained `.pth` model file

### 1 — Get your Instagram session cookie

1. Open Chrome → go to **instagram.com** → log in
2. Press **F12** → **Application** tab → **Cookies** → `https://www.instagram.com`
3. Find the `sessionid` cookie → copy its **Value**
4. Paste it into `.env` as `INSTAGRAM_SESSION_ID=<value>`

> **Tip:** Use a dedicated Instagram account, not your personal one.

### 2 — Configure environment

```bash
cd backend
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://instaguard:instaguard_secret@db:5432/instaguard
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

SECRET_KEY=your-super-secret-key-change-this

APIFY_API_TOKEN=apify_api_...
INSTAGRAM_SESSION_ID=your-sessionid-cookie-value
MAX_POSTS=50

MODEL_PATH=./data/instaguard_model.pth
MODEL_DEVICE=cpu    # or "cuda" if you have a GPU
```

### 3 — Place your trained model

```bash
cp /path/to/your/model.pth ./data/instaguard_model.pth
```

The model must be a PyTorch `.pth` file containing either:
- A raw `state_dict`, **or**
- A checkpoint dict with key `"model_state_dict"`

### 4 — Start everything with Docker Compose

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Running without Docker (Development)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start PostgreSQL and Redis (or use Docker for just these):
docker-compose up db redis -d

# Copy and edit env
cp .env.example .env

# Run FastAPI
uvicorn app:app --reload --port 8000

# Run Celery worker (separate terminal)
celery -A tasks.scan_task.celery_app worker --loglevel=info --concurrency=2
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # starts on http://localhost:3000
```

---

## API Reference

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account (name, email, password) |
| POST | `/api/auth/login` | Email + password login → JWT |
| POST | `/api/auth/google` | Google OAuth → JWT |

### Scans

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scans` | Start a new scan `{"instagram_username": "target"}` |
| GET | `/api/scans` | List all scans for current user |
| GET | `/api/scans/{id}` | Get scan detail with all post results |
| DELETE | `/api/scans/{id}` | Delete scan |
| GET | `/api/scans/{id}/export` | Download PDF forensic report |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/utils/test-cookie` | Validate Instagram session cookie (no Apify credits) |

Full interactive docs: **http://localhost:8000/docs**

---

## Connecting Your Google Drive Model

If your model is on Google Drive:

```bash
# Option A: gdown
pip install gdown
gdown "https://drive.google.com/uc?id=YOUR_FILE_ID" -O ./data/instaguard_model.pth

# Option B: rclone (for large files)
rclone copy gdrive:/path/to/model.pth ./data/
```

---

## RAM-Only Protocol

InstaGuard strictly enforces in-memory processing:

1. Apify scrapes post metadata (URLs) → stored only as strings in PostgreSQL
2. Each image is fetched via `httpx` directly into a `bytes` object
3. The bytes are passed to the detector and **immediately deleted** (`del image_bytes`) after inference
4. Only a small base64 JPEG thumbnail (120×120px, 60% quality) is stored in the DB for UI display
5. The original full-resolution image bytes **never touch the filesystem**

---

## Refreshing the Instagram Session Cookie

The `sessionid` cookie expires periodically. When scans start failing:

1. Open Chrome → instagram.com → ensure you're logged in
2. F12 → **Application** → **Storage** → **Cookies** → `https://www.instagram.com`
3. Copy the **Value** of `sessionid`
4. Update `INSTAGRAM_SESSION_ID` in `.env`
5. Restart the API and worker

You can verify the cookie without using Apify credits:

```bash
curl -H "Authorization: Bearer <your-jwt>" http://localhost:8000/api/utils/test-cookie
```

---

## Model Training Notes

The `InstaGuardModel` in `core/detector.py` expects:

- **Input:** RGB image tensors, resized to 224×224, normalized with ImageNet mean/std
- **Architecture:** `SRNetNoiseExtractor` (64-channel output) → 1×1 conv projection → `EfficientNet-B2`
- **Output:** 2-class logits `[clean_prob, stego_prob]`
- **Checkpoint format:** `torch.save(model.state_dict(), "instaguard_model.pth")`

To use a checkpoint saved with the full model dict:
```python
torch.save({"model_state_dict": model.state_dict(), "epoch": 50}, "checkpoint.pth")
```
Both formats are supported automatically.
