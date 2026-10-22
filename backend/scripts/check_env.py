"""
Cek konfigurasi environment sebelum menjalankan / deploy. Nilai rahasia tidak ditampilkan.

Pemakaian (dari folder backend):
  .\\.venv\\Scripts\\python.exe scripts\\check_env.py                     # cek backend/.env
  $env:ENV_FILE=".env.production"; .\\.venv\\Scripts\\python.exe scripts\\check_env.py   # cek production
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from prepare_database import catalog_counts, describe_database_url

REQUIRED = ("DATABASE_URL", "SESSION_SECRET", "GEMINI_API_KEY", "GEMINI_MODEL")
OPTIONAL = ("ALLOWED_ORIGINS", "RAPIDAPI_KEY", "FONNTE_TOKEN")


def check_variables() -> bool:
    ok = True
    for key in REQUIRED + OPTIONAL:
        filled = bool(os.getenv(key, "").strip())
        label = "terisi" if filled else ("KOSONG (wajib)" if key in REQUIRED else "kosong (opsional)")
        print(f"  {key:<18} {label}")
        ok &= filled or key not in REQUIRED
    return ok


def check_database(url: str, production: bool) -> bool:
    print(f"  Target : {describe_database_url(url)}")
    if production and url.startswith("sqlite"):
        print("  PERINGATAN: production memakai SQLite; data hilang setiap redeploy. Gunakan URL Neon.")
    if "neon.tech" in url and "-pooler" not in url:
        print("  PERINGATAN: pakai host '-pooler' dari Neon agar compute bisa scale to zero.")

    from sqlalchemy.exc import SQLAlchemyError
    from database.db_engine import engine
    try:
        counts = catalog_counts(engine)
    except SQLAlchemyError as exc:
        reason = str(getattr(exc, "orig", exc)).strip().splitlines()[0]
        print(f"  GAGAL terhubung: {reason}")
        return False
    print("  Terhubung.")
    for table, count in counts.items():
        print(f"    {table:<28} {'belum ada' if count is None else f'{count} baris'}")
    if any(not count for count in counts.values()):
        print("  Katalog belum lengkap. Jalankan scripts\\prepare_database.py dengan ENV_FILE yang sama.")
    return True


def check_gemini(api_key: str, model: str) -> bool:
    from google import genai
    try:
        client = genai.Client(api_key=api_key)
        available = [m.name.removeprefix("models/") for m in client.models.list()]
        if model not in available:
            flash = sorted(name for name in available if "flash" in name)
            print(f"  Model '{model}' tidak tersedia. Pilihan flash: {', '.join(flash) or '-'}")
            return False
        reply = client.models.generate_content(model=model, contents="Balas hanya dengan kata: OK")
    except Exception as exc:  # error dari SDK berbeda-beda (key salah, kuota, jaringan)
        print(f"  GAGAL: {str(exc).strip().splitlines()[0][:200]}")
        return False
    print(f"  API key valid, model '{model}' menjawab: {(reply.text or '').strip()[:40]}")
    return True


def skipped(key: str) -> bool:
    print(f"  Dilewati: {key} masih kosong.")
    return False


def main() -> int:
    from config import APP_ENV, DATABASE_URL, ENV_FILE, GEMINI_API_KEY, GEMINI_MODEL, MAINTENANCE_MODE

    print(f"File env : {ENV_FILE.name} ({'ada' if ENV_FILE.exists() else 'TIDAK DITEMUKAN'})")
    print(f"APP_ENV  : {APP_ENV}  |  MAINTENANCE_MODE: {MAINTENANCE_MODE}")

    print("\n[1] Variabel")
    results = [check_variables()]

    print("\n[2] Database")
    results.append(check_database(DATABASE_URL, APP_ENV == "production") if DATABASE_URL else skipped("DATABASE_URL"))

    print("\n[3] Gemini")
    results.append(check_gemini(GEMINI_API_KEY, GEMINI_MODEL) if GEMINI_API_KEY else skipped("GEMINI_API_KEY"))

    print("\nHASIL:", "SIAP" if all(results) else "BELUM SIAP - perbaiki bagian yang GAGAL/KOSONG di atas")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
