"""
Router: /api/whatsapp
Endpoints untuk integrasi WhatsApp melalui Fonnte API.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated, List, Literal, Optional, Union
from config import FONNTE_TOKEN
from auth import get_current_user
from database.db_models import User
from rate_limit import RateLimiter
from routers.users import normalize_phone

logger = logging.getLogger(__name__)
router = APIRouter()

# Nomor tujuan belum diverifikasi, jadi batasi jumlah kiriman per akun: 5 pesan per jam
_send_limiter = RateLimiter(limit=5, window=60 * 60)

class WorkoutExercise(BaseModel):
    name: str = Field(..., max_length=100)
    # AI kadang menulis set sebagai rentang teks, mis. "3-4"
    sets: Union[int, Annotated[str, Field(max_length=20)]] = Field(..., union_mode="left_to_right")
    reps: Union[int, Annotated[str, Field(max_length=50)]] = Field(..., union_mode="left_to_right")


class WorkoutDay(BaseModel):
    day: str = Field(..., max_length=50)
    focus: str = Field(..., max_length=100)
    exercises: List[WorkoutExercise] = Field(..., max_length=30)


class MealFood(BaseModel):
    name: str = Field(..., max_length=100)
    portion: str = Field(..., max_length=50)
    calories: Union[int, float] = Field(..., union_mode="left_to_right")


class MealEntry(BaseModel):
    meal_name: str = Field(..., max_length=100)
    time: Optional[str] = Field(None, max_length=30)
    foods: List[MealFood] = Field(..., max_length=30)


class WhatsAppSendRequest(BaseModel):
    plan_type: Literal["workout", "meal"]
    title: str = Field(..., max_length=100)
    schedule: Optional[List[WorkoutDay]] = Field(None, max_length=14)
    meals: Optional[List[MealEntry]] = Field(None, max_length=20)

def format_workout_message(plan: WhatsAppSendRequest) -> str:
    msg = f"🏋️ *FITMIND AI: {plan.title}* 🏋️\n\n"
    if not plan.schedule:
        return msg + "Jadwal kosong."
        
    for s in plan.schedule:
        msg += f"🗓️ *{s.day} - {s.focus}*\n"
        for ex in s.exercises:
            msg += f"  • {ex.name}: {ex.sets} set x {ex.reps}\n"
        msg += "\n"
    
    msg += "💪 Semangat latihannya!\n_Pesan ini dikirim otomatis oleh FitMind AI._"
    return msg

def format_meal_message(plan: WhatsAppSendRequest) -> str:
    msg = f"🥗 *FITMIND AI: {plan.title}* 🥗\n\n"
    if not plan.meals:
        return msg + "Jadwal kosong."
        
    for m in plan.meals:
        msg += f"⏰ *{m.time or ''} - {m.meal_name}*\n"
        for food in m.foods:
            msg += f"  • {food.name} ({food.portion}): {food.calories} kkal\n"
        msg += "\n"
    
    msg += "🍎 Ingat minum air yang cukup!\n_Pesan ini dikirim otomatis oleh FitMind AI._"
    return msg

@router.post("/send-plan")
async def send_plan_whatsapp(request: WhatsAppSendRequest, current_user: User = Depends(get_current_user)):
    """
    Format JSON plan ke teks dan kirim via WhatsApp (Fonnte).
    """
    if not FONNTE_TOKEN or FONNTE_TOKEN == "ISI_TOKEN_FONNTE_ANDA_DISINI":
        raise HTTPException(status_code=400, detail="Fonnte Token belum dikonfigurasi di .env")
        
    retry_after = _send_limiter.retry_after(str(current_user.id))
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Batas pengiriman WhatsApp tercapai. Coba lagi nanti.",
            headers={"Retry-After": str(retry_after)},
        )

    # 1. Bersihkan nomor HP (pastikan mulai dari 08 atau 628)
    if not (current_user.phone or "").strip():
        raise HTTPException(status_code=400, detail="Nomor WhatsApp akun belum tersedia.")
    # Akun lama bisa menyimpan nomor yang belum tervalidasi (mis. beberapa nomor dipisah koma)
    phone = normalize_phone(current_user.phone)
    if not phone:
        raise HTTPException(status_code=400, detail="Nomor WhatsApp akun tidak valid.")
    if phone.startswith("0"):
        phone = "62" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    # 2. Format pesan sesuai tipe
    if request.plan_type == "workout":
        message_text = format_workout_message(request)
    else:
        message_text = format_meal_message(request)
    if len(message_text) > 10000:
        raise HTTPException(status_code=422, detail="Pesan rencana terlalu panjang.")

    # 3. Kirim via Fonnte API
    url = "https://api.fonnte.com/send"
    headers = {
        "Authorization": FONNTE_TOKEN
    }
    data = {
        "target": phone,
        "message": message_text,
        "countryCode": "62", # Default Indonesia
    }

    _send_limiter.hit(str(current_user.id))
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, data=data, timeout=15.0)
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get("status") is True:
                    return {"success": True, "message": "Pesan berhasil dikirim ke WhatsApp."}
                else:
                    logger.error("Fonnte menolak permintaan pengiriman")
                    raise HTTPException(status_code=400, detail="Pengiriman WhatsApp ditolak oleh layanan.")
            else:
                logger.error("Fonnte HTTP error: %s", resp.status_code)
                raise HTTPException(status_code=502, detail="Gagal terhubung ke layanan WhatsApp.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error sending WA")
        raise HTTPException(status_code=502, detail="Gagal mengirim WhatsApp.") from e
