"""
FitMind AI - Database Engine & Session Manager
Mengelola koneksi SQLite (dev) / PostgreSQL (prod) dengan SQLAlchemy.
"""
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# ==============================================================
# Engine
# ==============================================================
# SQLite butuh check_same_thread; PostgreSQL (Neon) diberi batas waktu koneksi
# agar request cepat gagal dan mode maintenance aktif saat database tidak tersedia.
if DATABASE_URL.startswith("sqlite"):
    _engine_options = {"connect_args": {"check_same_thread": False}}
else:
    _engine_options = {"connect_args": {"connect_timeout": 10}, "pool_recycle": 300}
    if DATABASE_URL.startswith("postgresql+psycopg:"):
        # psycopg 3: matikan prepared statement otomatis agar aman lewat PgBouncer (pooler Neon)
        _engine_options["connect_args"]["prepare_threshold"] = None

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # deteksi koneksi yang sudah mati sebelum dipakai
    echo=False,               # set True untuk debug SQL queries
    **_engine_options,
)

# Aktifkan Foreign Key enforcement pada SQLite (by default SQLite mematikannya)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ==============================================================
# Session Factory
# ==============================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ==============================================================
# Dependency Injection (untuk FastAPI)
# ==============================================================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency untuk mendapatkan DB session per-request.
    Gunakan sebagai: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==============================================================
# Init DB (buat semua tabel jika belum ada)
# ==============================================================
def init_db():
    """Buat semua tabel sesuai model. Dipanggil saat startup."""
    from database.db_models import Base
    logger.info("Inisialisasi database — membuat tabel yang belum ada...")
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        if "avatar_data" not in {column["name"] for column in inspect(connection).get_columns("users")}:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN avatar_data TEXT")
    logger.info("Database siap.")
