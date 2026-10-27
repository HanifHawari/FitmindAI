"""
Router: /api/users
Manajemen akun dan data pribadi pengguna.

Alur:
  POST /api/users/login  → verifikasi password dan terbitkan token sesi
  GET  /api/users/{username}/profile   → ambil profil kebugaran
  PUT  /api/users/{username}/profile   → simpan / update profil kebugaran
  GET  /api/users/{username}/sessions  → daftar sesi chat user
  GET  /api/users/{username}/sessions/{session_id}/messages → riwayat pesan sesi
  DELETE /api/users/{username}/sessions/{session_id}        → hapus sesi
"""
import logging
import base64
import binascii
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.db_engine import get_db
from database.db_models import User, UserProfile, ChatSession, ChatMessage
from auth import create_access_token, get_current_user
from models import (
    APIResponse, AvatarUpdate, UserCreate, UserProfileUpdate,
    UserResponse
)
from rate_limit import RateLimiter
import bcrypt

logger = logging.getLogger(__name__)
router = APIRouter()

# Handler di file ini memakai `def` biasa: query database dan bcrypt bersifat blocking,
# sehingga FastAPI menjalankannya di threadpool dan event loop tetap melayani request lain.

# Batasi tebakan password: 10 kali gagal per username dalam 15 menit
_login_failures = RateLimiter(limit=10, window=15 * 60)
# Dicocokkan saat username tidak ada agar waktu respons tidak membocorkan username terdaftar
_DUMMY_HASH = bcrypt.hashpw(b"fitmind-dummy-password", bcrypt.gensalt())
# Satu nomor saja, 8-15 digit (opsional diawali +); mencegah daftar nomor dipakai sebagai target WhatsApp
_PHONE_PATTERN = re.compile(r"^\+?\d{8,15}$")


# ==============================================================
# Helper
# ==============================================================

def normalize_phone(phone: str) -> str:
    """Hapus spasi/strip lalu validasi format nomor. Kembalikan string kosong jika tidak valid."""
    cleaned = re.sub(r"[\s-]", "", phone or "")
    return cleaned if _PHONE_PATTERN.fullmatch(cleaned) else ""


def _get_owned_user(username: str, current_user: User) -> User:
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="Akses ke akun ini ditolak.")
    return current_user


def _compute_bmi(weight_kg: Optional[float], height_m: Optional[float]) -> Optional[float]:
    if weight_kg and height_m and height_m > 0:
        return round(weight_kg / (height_m ** 2), 2)
    return None


# ==============================================================
# POST /login — get-or-create user
# ==============================================================
@router.post("/login", response_model=UserResponse)
def login(body: UserCreate, db: Session = Depends(get_db)):
    """
    Masuk berdasarkan username dan password.
    Gagal → 401; terlalu banyak percobaan gagal → 429.
    """
    username = body.username.strip()
    limit_key = username.lower()
    retry_after = _login_failures.retry_after(limit_key)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak percobaan login. Coba lagi beberapa menit lagi.",
            headers={"Retry-After": str(retry_after)},
        )

    existing = db.query(User).filter(User.username == username).first()
    password_bytes = body.password.encode("utf-8")
    stored_hash = existing.password_hash.encode("utf-8") if existing and existing.password_hash else _DUMMY_HASH
    password_ok = len(password_bytes) <= 72 and bcrypt.checkpw(password_bytes, stored_hash)

    if not existing or not existing.password_hash or not password_ok:
        _login_failures.hit(limit_key)
        raise HTTPException(status_code=401, detail="Username atau password salah.")

    _login_failures.reset(limit_key)
    logger.info(f"User login: '{username}' (id={existing.id})")
    return UserResponse(
        id=existing.id,
        username=existing.username,
        phone=existing.phone,
        is_new=False,
        has_profile=existing.profile is not None,
        token=create_access_token(existing),
        avatar_data=existing.avatar_data,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        phone=current_user.phone,
        is_new=False,
        has_profile=current_user.profile is not None,
        avatar_data=current_user.avatar_data,
    )


@router.put("/me/avatar", response_model=APIResponse)
def save_avatar(
    body: AvatarUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefix = "data:image/jpeg;base64,"
    if not body.data_url.startswith(prefix):
        raise HTTPException(status_code=400, detail="Foto harus berformat JPEG.")
    try:
        image = base64.b64decode(body.data_url[len(prefix):], validate=True)
    except binascii.Error:
        raise HTTPException(status_code=400, detail="Data foto tidak valid.") from None
    if len(image) > 256 * 1024 or not image.startswith(b"\xff\xd8\xff") or not image.endswith(b"\xff\xd9"):
        raise HTTPException(status_code=400, detail="Foto JPEG tidak valid atau melebihi 256 KB.")
    current_user.avatar_data = body.data_url
    db.commit()
    return APIResponse(data={"avatar_data": current_user.avatar_data})


@router.delete("/me/avatar", response_model=APIResponse)
def delete_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.avatar_data = None
    db.commit()
    return APIResponse(message="Foto profil dihapus.")

@router.post("/register", response_model=UserResponse)
def register(body: UserCreate, db: Session = Depends(get_db)):
    """
    Daftar berdasarkan username.
    Jika sudah ada → 400.
    """
    username = body.username.strip()
    existing = db.query(User).filter(User.username == username).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar. Silakan login.")

    if len(body.password) < 8 or len(body.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password harus 8–72 byte.")

    if not body.phone:
        raise HTTPException(status_code=400, detail="Nomor WhatsApp wajib diisi untuk keamanan automation.")
    phone = normalize_phone(body.phone)
    if not phone:
        raise HTTPException(status_code=400, detail="Nomor WhatsApp tidak valid. Gunakan satu nomor, misalnya 081234567890.")

    hashed_password = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    # Buat user baru
    new_user = User(username=username, phone=phone, password_hash=hashed_password)
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        # Dua pendaftaran username yang sama di waktu bersamaan
        db.rollback()
        raise HTTPException(status_code=400, detail="Username sudah terdaftar. Silakan login.") from None
    db.refresh(new_user)
    logger.info(f"User baru dibuat: '{username}' (id={new_user.id})")

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        phone=new_user.phone,
        is_new=True,
        has_profile=False
    )


# ==============================================================
# GET /profile — ambil profil kebugaran
# ==============================================================
@router.get("/{username}/profile")
def get_profile(username: str, current_user: User = Depends(get_current_user)):
    """Ambil profil kebugaran user. 404 jika user belum ada, 204 jika profil belum diisi."""
    user = _get_owned_user(username, current_user)

    if not user.profile:
        return APIResponse(success=True, data=None,
                           message="Profil belum diisi. Gunakan PUT untuk mengisinya.")

    profile = user.profile
    return APIResponse(success=True, data={
        "user_id":           user.id,
        "username":          user.username,
        "age":               profile.age,
        "gender":            profile.gender,
        "weight_kg":         profile.weight_kg,
        "height_m":          profile.height_m,
        "bmi":               profile.bmi,
        "goal":              profile.goal,
        "experience_level":  profile.experience_level,
        "workout_frequency": profile.workout_frequency,
        "session_duration":  profile.session_duration,
        "workout_type":      profile.workout_type,
        "equipment":         profile.equipment,
        "diet_type":         profile.diet_type,
        "allergens": {
            "no_gluten": profile.no_gluten,
            "no_dairy":  profile.no_dairy,
            "no_nuts":   profile.no_nuts,
            "no_soy":    profile.no_soy,
            "no_eggs":   profile.no_eggs,
            "no_fish":   profile.no_fish,
        },
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    })


# ==============================================================
# PUT /profile — simpan / update profil
# ==============================================================
@router.put("/{username}/profile")
def upsert_profile(
    username: str,
    body: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simpan atau update profil kebugaran user.
    Jika profil sudah ada → update kolom yang dikirim saja.
    Jika belum ada → buat profil baru.
    """
    user = _get_owned_user(username, current_user)

    profile = user.profile
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    # Update field yang dikirim (tidak overwrite dengan None jika tidak dikirim)
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(profile, field, value)

    # Hitung BMI otomatis
    profile.bmi = _compute_bmi(profile.weight_kg, profile.height_m)

    db.commit()
    db.refresh(profile)
    logger.info(f"Profil diupdate: '{username}'")

    return APIResponse(
        success=True,
        message="Profil berhasil disimpan.",
        data={"bmi": profile.bmi}
    )


# ==============================================================
# GET /sessions — daftar sesi chat user
# ==============================================================
@router.get("/{username}/sessions")
def get_sessions(
    username: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil daftar sesi chat user (terbaru dulu)."""
    user = _get_owned_user(username, current_user)

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())
        .limit(limit)
        .all()
    )

    return APIResponse(
        success=True,
        total=len(sessions),
        data=[{
            "id":            s.id,
            "title":         s.title or "Sesi tanpa judul",
            "last_intent":   s.last_intent,
            "message_count": s.message_count,
            "created_at":    s.created_at.isoformat() if s.created_at else None,
            "updated_at":    s.updated_at.isoformat() if s.updated_at else None,
        } for s in sessions]
    )


# ==============================================================
# GET /sessions/{session_id}/messages — riwayat pesan
# ==============================================================
@router.get("/{username}/sessions/{session_id}/messages")
def get_session_messages(
    username: str,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil semua pesan dalam satu sesi chat."""
    user = _get_owned_user(username, current_user)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )

    return APIResponse(
        success=True,
        total=len(messages),
        data={
            "session": {
                "id":    session.id,
                "title": session.title or "Sesi tanpa judul",
            },
            "messages": [{
                "id":         m.id,
                "role":       m.role,
                "content":    m.content,
                "intent":     m.intent,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            } for m in messages]
        }
    )


# ==============================================================
# DELETE /sessions/{session_id} — hapus sesi
# ==============================================================
@router.delete("/{username}/sessions/{session_id}")
def delete_session(
    username: str,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hapus sesi chat beserta semua pesannya."""
    user = _get_owned_user(username, current_user)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")

    db.delete(session)
    db.commit()
    logger.info(f"Sesi {session_id} dihapus oleh '{username}'")

    return APIResponse(success=True, message=f"Sesi '{session.title}' berhasil dihapus.")
