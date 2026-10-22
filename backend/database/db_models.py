"""
FitMind AI - model SQLAlchemy untuk akun, percakapan, dan data kebugaran.

CSV diimpor ke tabel dataset melalui scripts/migrate_csv_to_sql.py.
"""
from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer,
    String, Text, DateTime, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ==============================================================
# 1. USERS — identitas minimal, tanpa password
# ==============================================================
class User(Base):
    """
    Satu baris = satu user yang pernah menggunakan aplikasi.
    Identifikasi hanya berdasarkan username (unik).
    Jika username sudah ada → user lama dilanjutkan.
    Jika username belum ada → user baru dibuat otomatis.
    """
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(100), unique=True, nullable=False, index=True)
    phone      = Column(String(20), unique=False, nullable=True) # WhatsApp number
    password_hash = Column(String(255), nullable=True)
    avatar_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    profile       = relationship("UserProfile", back_populates="user",
                                 uselist=False, cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user",
                                 cascade="all, delete-orphan",
                                 order_by="ChatSession.created_at.desc()")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# ==============================================================
# 2. USER PROFILES — profil kebugaran + alergen
# ==============================================================
class UserProfile(Base):
    """
    Profil kebugaran personal user. Relasi 1-to-1 dengan User.
    Alergen disimpan sebagai kolom boolean langsung (tidak tabel terpisah)
    karena jumlahnya tetap dan sudah diketahui (6 jenis).
    """
    __tablename__ = "user_profiles"

    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                               nullable=False, unique=True)

    # Data fisik
    age               = Column(Integer)
    gender            = Column(String(10))           # male / female
    weight_kg         = Column(Float)
    height_m          = Column(Float)
    bmi               = Column(Float)                # dihitung: weight / height^2

    # Preferensi latihan
    goal              = Column(String(50))           # weight_loss / muscle_gain / maintenance / endurance
    experience_level  = Column(String(20))           # beginner / intermediate / advanced
    workout_frequency = Column(Integer)              # hari per minggu
    session_duration  = Column(Float)                # jam per sesi
    workout_type      = Column(String(50))           # HIIT / Cardio / Strength / Yoga / Mixed
    equipment         = Column(String(100))          # Full Gym / Dumbbells / Bodyweight / Garage Gym

    # Preferensi diet
    diet_type         = Column(String(30))           # vegan / vegetarian / keto / paleo / none

    # Pantangan alergen (boolean langsung)
    no_gluten         = Column(Boolean, default=False)
    no_dairy          = Column(Boolean, default=False)
    no_nuts           = Column(Boolean, default=False)
    no_soy            = Column(Boolean, default=False)
    no_eggs           = Column(Boolean, default=False)
    no_fish           = Column(Boolean, default=False)

    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, goal='{self.goal}')>"


# ==============================================================
# 3. CHAT SESSIONS — pengelompokan percakapan
# ==============================================================
class ChatSession(Base):
    """
    Satu sesi = satu thread percakapan (berisi banyak pesan).
    Satu user bisa punya banyak sesi (misal: sesi hari Senin, sesi hari Selasa).
    """
    __tablename__ = "chat_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    title         = Column(String(100))          # 50 char pertama dari pesan pertama user
    last_intent   = Column(String(50))           # intent terakhir yang terdeteksi LLM
    message_count = Column(Integer, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user     = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session",
                            cascade="all, delete-orphan",
                            order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


# ==============================================================
# 4. CHAT MESSAGES — isi pesan tanya-jawab
# ==============================================================
class ChatMessage(Base):
    """
    Satu baris = satu pesan dalam sebuah sesi.
    role: 'user' (pesan dari user) atau 'assistant' (jawaban AI).
    """
    __tablename__ = "chat_messages"
    __table_args__ = (
        # Index composite untuk query riwayat chat yang efisien
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                        nullable=False)
    role       = Column(String(10), nullable=False)   # user / assistant
    content    = Column(Text, nullable=False)
    intent     = Column(String(50))                   # intent yang terdeteksi (nullable)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        preview = self.content[:40] if self.content else ''
        return f"<ChatMessage(id={self.id}, role='{self.role}', preview='{preview}...')>"


# ==============================================================
# 5. DATASET MODELS (Migrated from CSV)
# ==============================================================

class DBWorkout(Base):
    __tablename__ = "dataset_workout"
    id = Column(Integer, primary_key=True, index=True)
    body_part = Column(Text, index=True)
    type_of_muscle = Column(Text, index=True)
    workout = Column(Text)
    sets = Column(Text)
    reps_per_set = Column(Text)
    
    # Precomputed lower
    _body_part_lower = Column(Text, index=True)
    _type_of_muscle_lower = Column(Text, index=True)

class DBMasterNutrition(Base):
    __tablename__ = "dataset_master_nutrition"
    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(Text)
    calories = Column(Float)
    protein_g = Column(Float)
    fat_g = Column(Float)
    carbs_g = Column(Float)
    fiber_g = Column(Float)
    sugar_g = Column(Float)
    sodium_mg = Column(Float)
    health_score = Column(Float, index=True)
    food_type = Column(Text, index=True)
    source = Column(Text)
    contains_gluten = Column(Boolean, default=False)
    contains_dairy = Column(Boolean, default=False)
    contains_nuts = Column(Boolean, default=False)
    contains_soy = Column(Boolean, default=False)
    contains_eggs = Column(Boolean, default=False)
    contains_fish = Column(Boolean, default=False)
    
    # Precomputed lower
    _food_name_lower = Column(Text)

class DBHealthyFood(Base):
    __tablename__ = "dataset_healthy_foods"
    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(Text)
    food_type = Column(Text)
    calories = Column(Float)
    protein_g = Column(Float)
    fat_g = Column(Float)
    carbs_g = Column(Float)
    fiber_g = Column(Float)
    sugar_g = Column(Float)
    sodium_mg = Column(Float)
    health_score = Column(Float)
    
    # Precomputed lower
    _food_name_lower = Column(Text)

class DBProgramSummary(Base):
    __tablename__ = "dataset_program_summary"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text)
    description = Column(Text)
    level = Column(Text, index=True)
    goal = Column(Text, index=True)
    equipment = Column(Text, index=True)
    program_length = Column(Text)
    time_per_workout = Column(Text)
    total_exercises = Column(Integer)
    created = Column(Text)
    last_edit = Column(Text)
    
    # Precomputed number
    _weeks_num = Column(Integer, index=True)
