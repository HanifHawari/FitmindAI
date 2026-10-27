"""
FitMind AI - Pydantic Models (Request & Response Schemas)
"""
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Optional, List


# ==============================================================
# Chat Models
# ==============================================================

class ChatMessage(BaseModel):
    # Riwayat ikut berisi jawaban AI yang bisa jauh lebih panjang dari pesan user
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=20000, description="Isi pesan")


class UserProfile(BaseModel):
    """Profil user yang disimpan di localStorage frontend."""
    name: Optional[str] = Field(None, max_length=50)
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = Field(None, max_length=10)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    height_m: Optional[float] = Field(None, gt=0, le=3)
    bmi: Optional[float] = Field(None, ge=0, le=200)
    goal: Optional[str] = Field(None, max_length=50)  # weight_loss | muscle_gain | maintenance | endurance
    experience_level: Optional[str] = Field(None, max_length=20)  # beginner | intermediate | advanced
    workout_frequency: Optional[int] = Field(None, ge=0, le=14)  # hari/minggu
    session_duration: Optional[float] = Field(None, ge=0, le=1440)  # menit/sesi
    workout_type: Optional[str] = Field(None, max_length=50)  # HIIT | Cardio | Strength | Yoga | Mixed
    equipment: Optional[str] = Field(None, max_length=100)
    # Alergen
    no_gluten: Optional[bool] = False
    no_dairy: Optional[bool] = False
    no_nuts: Optional[bool] = False
    no_soy: Optional[bool] = False
    no_eggs: Optional[bool] = False
    no_fish: Optional[bool] = False
    # Diet
    diet_type: Optional[str] = Field(None, max_length=30)  # vegan | vegetarian | keto | paleo | none


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=50)
    user_profile: Optional[UserProfile] = None


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None


# ==============================================================
# Generic Response
# ==============================================================

class APIResponse(BaseModel):
    success: bool = True
    data: Optional[object] = None
    message: Optional[str] = None
    total: Optional[int] = None


# ==============================================================
# User & Session Schemas (untuk DB)
# ==============================================================

class UserCreate(BaseModel):
    """Request body untuk pendaftaran dan login."""
    username: str = Field(..., min_length=2, max_length=30,
                          pattern=r"^[a-zA-Z0-9_.-]+$",
                          description="Nama unik user (hanya huruf, angka, dot, strip, underscore. Tanpa spasi.)")
    password: str = Field(..., min_length=1, max_length=72, description="Password user")
    phone: Optional[str] = Field(None, max_length=25, description="Nomor WhatsApp (misal: 08123456789)")


class UserProfileUpdate(BaseModel):
    """Request body untuk menyimpan / update profil kebugaran user.
    Panjang teks mengikuti ukuran kolom di tabel user_profiles."""
    age:               Optional[int]   = Field(None, ge=1, le=120)
    gender:            Optional[str]   = Field(None, max_length=10)   # male / female
    weight_kg:         Optional[float] = Field(None, gt=0, le=500)
    height_m:          Optional[float] = Field(None, gt=0, le=3)
    goal:              Optional[str]   = Field(None, max_length=50)   # weight_loss | muscle_gain | maintenance | endurance
    experience_level:  Optional[str]   = Field(None, max_length=20)   # beginner | intermediate | advanced
    workout_frequency: Optional[int]   = Field(None, ge=0, le=14)
    session_duration:  Optional[float] = Field(None, ge=0, le=1440)
    workout_type:      Optional[str]   = Field(None, max_length=50)
    equipment:         Optional[str]   = Field(None, max_length=100)
    diet_type:         Optional[str]   = Field(None, max_length=30)
    no_gluten:         Optional[bool]  = False
    no_dairy:          Optional[bool]  = False
    no_nuts:           Optional[bool]  = False
    no_soy:            Optional[bool]  = False
    no_eggs:           Optional[bool]  = False
    no_fish:           Optional[bool]  = False


class UserResponse(BaseModel):
    """Response setelah pendaftaran atau login."""
    id:         int
    username:   str
    phone:      Optional[str]
    is_new:     bool  # True jika baru dibuat, False jika sudah ada
    has_profile: bool
    token: Optional[str] = None
    avatar_data: Optional[str] = None

    class Config:
        from_attributes = True


class AvatarUpdate(BaseModel):
    data_url: str = Field(..., max_length=350_000)


# Extend ChatRequest untuk mendukung session_id (opsional)
class ChatRequestDB(BaseModel):
    """Chat request yang menyimpan pesan ke database."""
    message:    str             = Field(..., min_length=1, max_length=2000)
    username:   str             = Field(..., min_length=2, max_length=30,
                                        pattern=r"^[a-zA-Z0-9_.-]+$",
                                        description="Username untuk identifikasi user (tanpa spasi)")
    session_id: Optional[int]   = Field(None, description="ID sesi (None = buat sesi baru)")
    history:    List[ChatMessage] = Field(default_factory=list, max_length=50)
    user_profile: Optional[UserProfile] = None


# ==============================================================
# Plan Generation Models (Structured Output)
# ==============================================================

class PlanGenerateRequest(BaseModel):
    """Request untuk generate workout / meal plan terstruktur."""
    plan_type: Optional[str] = Field("workout", max_length=20, description="'workout' atau 'meal'")
    goal: Optional[str] = Field(None, max_length=50, description="weight_loss | muscle_gain | maintenance | endurance")
    level: Optional[str] = Field(None, max_length=30, description="beginner | intermediate | advanced")
    days_per_week: Optional[int] = Field(3, ge=1, le=7, description="Jumlah hari latihan per minggu")
    equipment: Optional[str] = Field(None, max_length=100, description="Full Gym | Dumbbells | Bodyweight")
    diet_type: Optional[str] = Field(None, max_length=30, description="vegan | vegetarian | keto | paleo | normal")
    allergies: Optional[List[Annotated[str, Field(max_length=50)]]] = Field(
        default_factory=list, max_length=10, description="Daftar alergen")
    notes: Optional[str] = Field(None, max_length=1000, description="Catatan tambahan dari user")

