"""
Buat tabel & isi katalog (nutrisi, program, workout, makanan sehat) dari dataset CSV.
Aman dijalankan berulang: katalog yang sudah terisi dilewati.

Pemakaian (dari folder backend):
  .\\.venv\\Scripts\\python.exe scripts\\prepare_database.py                    # database di backend/.env
  $env:ENV_FILE=".env.production"; .\\.venv\\Scripts\\python.exe scripts\\prepare_database.py   # Neon
"""
import logging
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.append(str(Path(__file__).resolve().parent.parent))

CATALOG_TABLES = ("dataset_master_nutrition", "dataset_program_summary", "dataset_workout", "dataset_healthy_foods")


def describe_database_url(url: str) -> str:
    """Tampilkan jenis & host database tanpa username/password."""
    if url.startswith("sqlite"):
        return url
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.hostname}{parts.path}"


def catalog_counts(engine) -> dict:
    from sqlalchemy import inspect, text
    existing = set(inspect(engine).get_table_names())
    with engine.connect() as connection:
        return {
            table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() if table in existing else None
            for table in CATALOG_TABLES
        }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    from config import DATABASE_URL, ENV_FILE

    if not DATABASE_URL:
        print(f"DATABASE_URL di {ENV_FILE.name} masih kosong.")
        return 1
    print(f"File env : {ENV_FILE.name}")
    print(f"Database : {describe_database_url(DATABASE_URL)}")

    from database.db_engine import engine
    from database.status import prepare_database

    if not prepare_database():
        print("Gagal menyiapkan database. Periksa DATABASE_URL dan koneksi internet.")
        return 1
    for table, count in catalog_counts(engine).items():
        print(f"  {table:<28} {count} baris")
    print("Selesai.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
