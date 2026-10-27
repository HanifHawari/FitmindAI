"""
Router: /api/dashboard
Statistik referensi dari dataset untuk dashboard & kalkulasi personal.
"""
from typing import Optional

from fastapi import APIRouter, Query

from data_loader import get_user_stats_summary
from models import APIResponse

router = APIRouter()


@router.get("/stats")
def get_dataset_stats():
    """Statistik agregat dari gym members dataset (referensi benchmarking)."""
    stats = get_user_stats_summary()
    return APIResponse(success=True, data=stats)


from database.db_engine import SessionLocal
from database.db_models import DBWorkout, DBMasterNutrition, DBProgramSummary

@router.get("/dataset-overview")
def get_dataset_overview():
    """Ringkasan semua dataset yang tersedia (Query DB)."""
    with SessionLocal() as db:
        workouts_count = db.query(DBWorkout).count()
        nutrition_count = db.query(DBMasterNutrition).count()
        programs_count = db.query(DBProgramSummary).count()

    overview = {
        "workout_exercises": workouts_count,
        "master_nutrition": nutrition_count,
        "programs": programs_count,
        "gym_members_profiles": 973,  # Hardcoded karena gym_members tidak di migrasi
    }
    return APIResponse(success=True, data=overview)


@router.get("/calculate-bmi")
async def calculate_bmi(
    weight_kg: float = Query(..., gt=0, le=500, description="Berat badan (kg)"),
    height_m: float = Query(..., gt=0, le=3, description="Tinggi badan (meter)"),
):
    """Hitung BMI dan kategori."""
    if height_m <= 0:
        return APIResponse(success=False, message="Tinggi badan tidak valid")

    bmi = round(weight_kg / (height_m ** 2), 2)

    if bmi < 18.5:
        category = "Underweight"
        color = "warning"
    elif bmi < 25:
        category = "Normal"
        color = "success"
    elif bmi < 30:
        category = "Overweight"
        color = "warning"
    else:
        category = "Obese"
        color = "danger"

    # Bandingkan dengan rata-rata dataset
    avg_bmi = 26.5

    return APIResponse(success=True, data={
        "bmi": bmi,
        "category": category,
        "color": color,
        "weight_kg": weight_kg,
        "height_m": height_m,
        "dataset_avg_bmi": avg_bmi,
        "ideal_weight_range": {
            "min": round(18.5 * (height_m ** 2), 1),
            "max": round(24.9 * (height_m ** 2), 1),
        }
    })


@router.get("/estimate-calories")
async def estimate_calories_burned(
    age: int = Query(..., ge=1, le=120, description="Usia"),
    weight_kg: float = Query(..., gt=0, le=500, description="Berat badan (kg)"),
    avg_bpm: int = Query(..., ge=20, le=250, description="Average heart rate selama sesi"),
    duration_hours: float = Query(..., gt=0, le=24, description="Durasi sesi (jam)"),
    workout_type: str = Query("Strength", max_length=20, description="HIIT | Cardio | Strength | Yoga"),
):
    """
    Estimasi kalori terbakar berdasarkan formula Keytel et al.
    Menggunakan gender-neutral formula.
    """
    # Formula estimasi kalori (dari jurnal Keytel et al. 2005)
    # VO2 max proxy formula
    calories_per_min = (
        (-55.0969 + 0.6309 * avg_bpm + 0.1988 * weight_kg + 0.2017 * age) / 4.184
    )
    duration_minutes = duration_hours * 60
    base_calories = calories_per_min * duration_minutes

    # Intensifier per workout type
    MULTIPLIERS = {
        "HIIT": 1.15,
        "Cardio": 1.05,
        "Strength": 0.95,
        "Yoga": 0.80,
        "Mixed": 1.0,
    }
    multiplier = MULTIPLIERS.get(workout_type, 1.0)
    estimated_calories = round(max(0, base_calories * multiplier), 1)

    # Bandingkan dengan avg dataset
    avg_burned = 890.0

    return APIResponse(success=True, data={
        "estimated_calories": estimated_calories,
        "duration_minutes": int(duration_minutes),
        "workout_type": workout_type,
        "multiplier_used": multiplier,
        "dataset_avg_calories_burned": avg_burned,
    })


@router.get("/bpm-analysis")
async def analyze_heart_rate(
    age: int = Query(..., ge=1, le=120, description="Usia pengguna"),
    avg_bpm: int = Query(..., ge=20, le=250, description="BPM rata-rata sesi"),
    max_bpm: Optional[int] = Query(None, ge=20, le=250, description="BPM maksimal sesi"),
    resting_bpm: Optional[int] = Query(None, ge=20, le=250, description="BPM istirahat"),
):
    """Analisis heart rate dan zona latihan."""
    max_hr_theory = 220 - age
    zones = {
        "Zone 1 (Recovery)": (0.50, 0.60),
        "Zone 2 (Fat Burn)": (0.60, 0.70),
        "Zone 3 (Cardio)": (0.70, 0.80),
        "Zone 4 (Anaerobic)": (0.80, 0.90),
        "Zone 5 (Max)": (0.90, 1.00),
    }

    # Tentukan zona dari avg_bpm
    current_zone = "Zone 1 (Recovery)"
    pct = avg_bpm / max_hr_theory
    for zone, (low, high) in zones.items():
        if low <= pct < high:
            current_zone = zone
            break

    zone_ranges = {
        zone: {
            "min_bpm": round(max_hr_theory * low),
            "max_bpm": round(max_hr_theory * high),
        }
        for zone, (low, high) in zones.items()
    }

    return APIResponse(success=True, data={
        "age": age,
        "theoretical_max_hr": max_hr_theory,
        "avg_bpm": avg_bpm,
        "avg_bpm_pct": round(pct * 100, 1),
        "current_zone": current_zone,
        "max_bpm": max_bpm,
        "resting_bpm": resting_bpm,
        "zones": zone_ranges,
    })
