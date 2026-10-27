from fastapi import APIRouter, Depends, Query, Response
from typing import Optional
from sqlalchemy.orm import Session

from data_loader import search_workout
from auth import get_current_user
from database.db_engine import get_db
from database.db_models import DBWorkout
from models import APIResponse
from exercise_api import search_by_name, search_by_body_part, get_exercise_detail, get_all_body_parts, fetch_exercise_gif, get_all_exercises_gif

router = APIRouter()


@router.get("", dependencies=[Depends(get_current_user)])
async def get_all_workouts():
    """Ambil semua data workout. (Backward compatibility untuk ExerciseDB)"""
    results = await get_all_exercises_gif(limit=24)
    if not results:
        return APIResponse(success=False, message="Dataset workout tidak tersedia")
    return APIResponse(
        success=True,
        data=results,
        total=len(results)
    )


@router.get("/search", dependencies=[Depends(get_current_user)])
async def search_workouts(
    body_part: Optional[str] = Query(None, max_length=50, description="Contoh: Chest, Back, Legs"),
    muscle: Optional[str] = Query(None, max_length=50, description="Contoh: Upper Chest, Hamstring"),
):
    """Cari workout berdasarkan body_part atau muscle group. (Backward compatibility)"""
    if body_part:
        results = await search_by_body_part(body_part, limit=24)
    elif muscle:
        results = await search_by_name(muscle, limit=24)
    else:
        results = await get_all_exercises_gif(limit=24)
    return APIResponse(success=True, data=results, total=len(results))


@router.get("/body-parts")
def get_body_parts(db: Session = Depends(get_db)):
    """Daftar unique body parts yang tersedia."""
    parts = [part for (part,) in db.query(DBWorkout.body_part).filter(DBWorkout.body_part.isnot(None)).distinct().all()]
    return APIResponse(success=True, data=parts, total=len(parts))


@router.get("/muscles")
def get_muscle_types(db: Session = Depends(get_db)):
    """Daftar unique muscle types yang tersedia."""
    muscles = [muscle for (muscle,) in db.query(DBWorkout.type_of_muscle).filter(DBWorkout.type_of_muscle.isnot(None)).distinct().all()]
    return APIResponse(success=True, data=muscles, total=len(muscles))


@router.get("/generate-split")
def generate_weekly_split(
    days: int = Query(3, ge=1, le=6, description="Hari latihan per minggu"),
    body_parts: Optional[str] = Query(None, description="Comma-separated: Chest,Back,Legs"),
    db: Session = Depends(get_db),
):
    """
    Generate weekly workout split berdasarkan jumlah hari.
    Logic: 1=Full Body, 2=Upper/Lower, 3=PPL, 4=Upper/Lower x2, 5-6=Body Part Split
    """
    if db.query(DBWorkout.id).first() is None:
        return APIResponse(success=False, message="Dataset tidak tersedia")

    # Mapping days → split
    SPLITS = {
        1: {"Full Body": None},
        2: {"Upper": ["Chest", "Back", "Shoulders", "Arms"],
            "Lower": ["Legs", "Abs"]},
        3: {"Push": ["Chest", "Shoulders"],
            "Pull": ["Back", "Arms"],
            "Legs": ["Legs", "Abs"]},
        4: {"Upper A": ["Chest", "Back"],
            "Lower A": ["Legs", "Abs"],
            "Upper B": ["Shoulders", "Arms"],
            "Lower B": ["Legs", "Abs"]},
        5: {"Chest": ["Chest"], "Back": ["Back"],
            "Legs": ["Legs"], "Shoulders": ["Shoulders"],
            "Arms + Abs": ["Arms", "Abs"]},
        6: {"Chest": ["Chest"], "Back": ["Back"], "Legs A": ["Legs"],
            "Shoulders": ["Shoulders"], "Arms": ["Arms"],
            "Legs B + Abs": ["Legs", "Abs"]},
    }

    split = SPLITS.get(days, SPLITS[3])

    result = {}
    for day_name, parts in split.items():
        if parts is None:
            # Full body
            all_exercises = search_workout()
            result[day_name] = all_exercises[:10]
        else:
            day_exercises = []
            for part in parts:
                exercises = search_workout(body_part=part)
                day_exercises.extend(exercises[:4])
            result[day_name] = day_exercises

    return APIResponse(success=True, data=result)


# ==============================================================
# ExerciseDB Endpoints (Animasi GIF gerakan)
# ==============================================================

@router.get("/gif/search", dependencies=[Depends(get_current_user)])
async def search_exercise_gif(
    q: str = Query(..., min_length=1, max_length=100, description="Nama gerakan, contoh: push up, squat, curl")
):
    """
    Cari latihan berdasarkan nama dari ExerciseDB.
    Response berisi gif_url untuk animasi gerakan.
    """
    results = await search_by_name(q, limit=12)
    if not results:
        return APIResponse(success=False, message="Latihan tidak ditemukan di ExerciseDB", data=[])
    return APIResponse(success=True, data=results, total=len(results))


@router.get("/gif/all", dependencies=[Depends(get_current_user)])
async def get_all_exercise_gifs(
    limit: int = Query(24, ge=1, le=100, description="Batas jumlah data yang dikembalikan")
):
    """
    Ambil semua latihan dari ExerciseDB.
    Response berisi gif_url untuk animasi gerakan.
    """
    results = await get_all_exercises_gif(limit=limit)
    if not results:
        return APIResponse(success=False, message="Latihan tidak ditemukan di ExerciseDB", data=[])
    return APIResponse(success=True, data=results, total=len(results))


@router.get("/gif/body-part", dependencies=[Depends(get_current_user)])
async def search_exercise_gif_by_body_part(
    body_part: str = Query(..., min_length=1, max_length=50, description="Body part, contoh: chest, back, legs, shoulders")
):
    """
    Ambil latihan berdasarkan body part dari ExerciseDB.
    Response berisi gif_url untuk animasi gerakan.
    """
    results = await search_by_body_part(body_part, limit=12)
    if not results:
        return APIResponse(success=False, message="Body part tidak ditemukan di ExerciseDB", data=[])
    return APIResponse(success=True, data=results, total=len(results))


@router.get("/gif/detail/{exercise_id}", dependencies=[Depends(get_current_user)])
async def get_exercise_gif_detail(exercise_id: str):
    """
    Ambil detail lengkap satu gerakan beserta instruksi step-by-step.
    """
    result = await get_exercise_detail(exercise_id)
    if not result:
        return APIResponse(success=False, message="Gerakan tidak ditemukan")
    return APIResponse(success=True, data=result)


@router.get("/gif/body-parts", dependencies=[Depends(get_current_user)])
async def list_gif_body_parts():
    """Daftar semua body part yang tersedia di ExerciseDB."""
    parts = await get_all_body_parts()
    return APIResponse(success=True, data=parts, total=len(parts))


@router.get("/gif/image/{exercise_id}")
async def proxy_exercise_gif(exercise_id: str):
    """
    Proxy endpoint: Ambil gambar GIF dari ExerciseDB menggunakan RapidAPI key,
    kemudian kirim ke frontend. Ini diperlukan karena ExerciseDB v2 gratis
    tidak menyertakan gifUrl langsung dalam response JSON.
    """
    gif_bytes = await fetch_exercise_gif(exercise_id)
    if gif_bytes:
        return Response(
            content=gif_bytes,
            media_type="image/gif",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache 1 hari
                "Access-Control-Allow-Origin": "*",
            }
        )
    # Jika GIF tidak tersedia, coba fallback ke GIF langsung via redirect
    return Response(status_code=404)
