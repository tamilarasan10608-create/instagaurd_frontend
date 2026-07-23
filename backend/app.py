from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from database import create_tables
from api.auth_router import router as auth_router
from api.scan_router import router as scan_router
from api.utils_router import router as utils_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    # Preload ML model in the API process (also loaded lazily in workers)
    from core.detector import load_model
    load_model()
    yield


app = FastAPI(
    title="InstaGuard API",
    description="Automated steganography detection for Instagram images.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(scan_router)
app.include_router(utils_router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=settings.ENVIRONMENT == "development")
