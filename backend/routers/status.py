"""
Router: /api/status
Status layanan untuk frontend — menentukan apakah mode maintenance ditampilkan.
Selalu membalas 200; kondisi layanan ada di field "status".
"""
import asyncio

from fastapi import APIRouter

from config import GEMINI_API_KEY, MAINTENANCE_MODE
from database.status import database_available, database_prepared, prepare_database_in_background

router = APIRouter()

# Batas tunggu cek database agar halaman tidak menunggu lama saat database tidak terjangkau.
# Jika lewat batas, pengecekan tetap selesai di thread-nya dan memperbarui cache.
_STATUS_WAIT_SECONDS = 5


@router.get("")
async def service_status():
    if MAINTENANCE_MODE:
        return {"status": "maintenance", "database": None, "ai": bool(GEMINI_API_KEY), "reason": "planned"}

    try:
        database_ok = await asyncio.wait_for(asyncio.to_thread(database_available), _STATUS_WAIT_SECONDS)
    except asyncio.TimeoutError:
        database_ok = False
    if database_ok and not database_prepared():
        # Database baru pulih: buat tabel & isi katalog dulu sebelum dibuka untuk user
        prepare_database_in_background()
        database_ok = False

    return {
        "status": "ok" if database_ok else "maintenance",
        "database": database_ok,
        "ai": bool(GEMINI_API_KEY),
        "reason": None if database_ok else "database",
    }
