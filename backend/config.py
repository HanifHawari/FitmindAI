"""
FitMind AI Backend - Configuration
Membaca environment variables dari .env file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env dari folder backend/.
# Set ENV_FILE=.env.production untuk memakai konfigurasi production dari komputer lokal
# (mis. import data ke Neon). Di Railway file ini tidak ada; variabel diambil dari dashboard.
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / os.getenv("ENV_FILE", ".env")
load_dotenv(ENV_FILE, override=True)

# ==============================================================
# Gemini API
# ==============================================================
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Anggaran "thinking" Gemini untuk AI Chat: 0 = dimatikan (token pertama ±1 detik, bukan 3-5 detik).
# Kosongkan untuk memakai default model (mis. model yang tidak menerima nilai 0). AI Plan tidak terpengaruh.
_thinking_budget = os.getenv("GEMINI_THINKING_BUDGET", "0").strip()
GEMINI_THINKING_BUDGET: int | None = int(_thinking_budget) if _thinking_budget else None

# ==============================================================
# Fonnte API (WhatsApp)
# ==============================================================
FONNTE_TOKEN: str = os.getenv("FONNTE_TOKEN", "")

# ==============================================================
# RapidAPI (ExerciseDB)
# ==============================================================
RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")

# ==============================================================
# App
# ==============================================================
APP_ENV: str = os.getenv("APP_ENV", "production")
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
# Railway menggunakan variabel environment bernama 'PORT', bukan 'APP_PORT'
APP_PORT: int = int(os.getenv("PORT", os.getenv("APP_PORT", "8000")))
# Saklar manual: true = tampilkan mode maintenance ke semua pengunjung
MAINTENANCE_MODE: bool = os.getenv("MAINTENANCE_MODE", "false").strip().lower() == "true"

# ==============================================================
# Dataset Paths (relatif dari backend/)
# ==============================================================
DATASET_BASE = Path(os.getenv("DATASET_BASE_PATH", "../dataset"))

WORKOUT_CSV       = DATASET_BASE / "gerakan" / "Workout.csv"
# Menggunakan Master Nutrition (Gabungan USDA, Healthy Foods, dan Allergens)
MASTER_NUTRITION_CSV = DATASET_BASE / "nutrisiAI" / "master_nutrition.csv"
# Healthy Foods Database untuk tab "Makanan Sehat"
HEALTHY_FOODS_CSV = DATASET_BASE / "nutrisiAI" / "healthy_foods_database.csv"
PROGRAMS_CSV      = DATASET_BASE / "program" / "program_summary.csv"

# ==============================================================
# ChromaDB
# ==============================================================
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))

# ==============================================================
# Database (SQLAlchemy)
# ==============================================================
# SQLite untuk development, PostgreSQL (Neon) untuk production.
# URL "postgresql://..." yang disalin dari Neon otomatis memakai driver psycopg (v3) yang terpasang.
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'fitmind.db'}"
)
for _prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(_prefix):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len(_prefix):]

# ==============================================================
# CORS
# ==============================================================
# Set ALLOWED_ORIGINS di Environment Variables, pisahkan dengan koma.
# Contoh: https://frontend-fitmind.vercel.app,http://localhost:5173
# Frontend production disajikan dari origin yang sama; Vite lokal perlu CORS.
_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
if _origins_raw == "*":
    ALLOWED_ORIGINS: list[str] = ["*"]
else:
    ALLOWED_ORIGINS: list[str] = [o.strip() for o in _origins_raw.split(",")]

