"""
FitMind AI - FastAPI Main Application
Startup → load datasets → register routers → run
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import InterfaceError, OperationalError, TimeoutError as PoolTimeoutError

from config import APP_ENV, APP_HOST, APP_PORT, ALLOWED_ORIGINS
from vector_store import init_vector_stores
from database.status import mark_database, prepare_database
from routers import chat, workout, nutrition, programs, dashboard, users, plans, calendar, whatsapp, status

# Direktori hasil build frontend (frontend/dist → di-copy ke backend/dist saat build)
FRONTEND_DIST = Path(__file__).parent / "dist"

# ==============================================================
# Logging Setup
# ==============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# ==============================================================
# Lifespan (startup & shutdown)
# ==============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inisialisasi database dan indeks vektor saat server startup."""
    logger.info("FitMind AI Backend starting...")
    # Jika database tidak bisa diakses, server tetap jalan dalam mode maintenance
    # dan /api/status akan menyiapkan database begitu koneksi pulih.
    prepare_database()
    init_vector_stores()
    logger.info("Server siap menerima request!")
    yield
    logger.info("👋 FitMind AI Backend shutting down...")


# ==============================================================
# App Instance
# ==============================================================
app = FastAPI(
    title="FitMind AI API",
    description="Backend API untuk FitMind AI — Gym & Nutrition LLM Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if APP_ENV == "production" else "/docs",
    redoc_url=None if APP_ENV == "production" else "/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(OperationalError)
@app.exception_handler(InterfaceError)
@app.exception_handler(PoolTimeoutError)
async def database_unavailable_handler(request: Request, exc: Exception):
    """Database tidak bisa diakses (mis. kuota Neon habis) → frontend menampilkan maintenance."""
    logger.error("Database tidak tersedia saat %s %s: %s", request.method, request.url.path, exc.__class__.__name__)
    mark_database(False)
    return JSONResponse(
        status_code=503,
        content={"detail": "Layanan sedang dalam pemeliharaan.", "maintenance": True},
    )

# ==============================================================
# Routers
# ==============================================================
app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(users.router,     prefix="/api/users",     tags=["Users"])
app.include_router(workout.router,   prefix="/api/workout",   tags=["Workout"])
app.include_router(nutrition.router, prefix="/api/nutrition", tags=["Nutrition"])
app.include_router(programs.router,  prefix="/api/programs",  tags=["Programs"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(plans.router,     prefix="/api/plans",     tags=["Plans"])
app.include_router(calendar.router,  prefix="/api/calendar",  tags=["Calendar"])
app.include_router(whatsapp.router,  prefix="/api/whatsapp",  tags=["WhatsApp"])
app.include_router(status.router,    prefix="/api/status",    tags=["Status"])


# ==============================================================
# Health Check (khusus API, tidak diganggu oleh SPA catch-all)
# ==============================================================
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
    }


# ==============================================================
# Static Files (Frontend React — hanya aktif jika sudah di-build)
# ==============================================================
if FRONTEND_DIST.exists():
    logger.info(f"Serving frontend dari: {FRONTEND_DIST}")
    # Serve file statis (JS, CSS, gambar, video, dll)
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # SPA catch-all: semua route yang bukan /api/* diarahkan ke index.html
    # Ini harus didaftarkan TERAKHIR agar tidak menimpa route API
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Cek apakah ada file statis langsung (favicon.ico, .mp4, .png, dll)
        dist_root = FRONTEND_DIST.resolve()
        file_path = (dist_root / full_path).resolve()
        if not file_path.is_relative_to(dist_root) or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        if file_path.is_file() and file_path.suffix.lower() in {".svg", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".ico"}:
            return FileResponse(file_path)
        # Fallback ke index.html untuk SPA routing (React Router)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    logger.warning("Frontend dist/ tidak ditemukan. Jalankan: cd frontend && npm run build")

    @app.get("/", tags=["Health"])
    async def root():
        return {"app": "FitMind AI", "version": "1.0.0", "status": "running", "docs": "/docs"}


# ==============================================================
# Entry Point
# ==============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_ENV != "production",
        log_level="info"
    )
