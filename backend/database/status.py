"""
FitMind AI - Status Database
Menentukan apakah database (mis. Neon) bisa diakses, untuk mode maintenance.
Tidak ada ping berkala di background agar compute Neon tetap bisa scale to zero.
"""
import logging
import threading
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database.catalog_seed import seed_catalogs
from database.db_engine import engine, init_db

logger = logging.getLogger(__name__)

_CACHE_SECONDS = 30
_state = {"ok": None, "checked_at": 0.0}
_prepared = False
_prepare_lock = threading.Lock()


def mark_database(ok: bool) -> None:
    """Simpan hasil cek terakhir (dipanggil juga saat request gagal karena database)."""
    _state["ok"] = ok
    _state["checked_at"] = time.monotonic()


def database_available(max_age: float = _CACHE_SECONDS) -> bool:
    """Cek koneksi dengan SELECT 1; hasilnya di-cache selama max_age detik."""
    if _state["ok"] is not None and time.monotonic() - _state["checked_at"] < max_age:
        return _state["ok"]
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Database tidak dapat diakses: %s", exc.__class__.__name__)
        mark_database(False)
        return False
    mark_database(True)
    return True


def database_prepared() -> bool:
    return _prepared


def prepare_database() -> bool:
    """Buat tabel dan isi katalog satu kali. Aman dipanggil ulang setelah database pulih."""
    global _prepared
    with _prepare_lock:
        if _prepared:
            return True
        try:
            init_db()
            seed_catalogs()
        except SQLAlchemyError as exc:
            logger.error("Database belum siap, server berjalan dalam mode maintenance: %s", exc)
            mark_database(False)
            return False
        _prepared = True
        mark_database(True)
        return True


def prepare_database_in_background() -> None:
    """Jalankan prepare_database() di thread terpisah jika belum berjalan."""
    if _prepared or _prepare_lock.locked():
        return
    threading.Thread(target=prepare_database, name="prepare-database", daemon=True).start()
