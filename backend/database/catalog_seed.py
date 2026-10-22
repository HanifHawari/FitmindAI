"""Isi katalog nutrisi, program, workout, dan makanan sehat dari CSV saat tabelnya masih kosong."""

import csv
import logging
import math
import re

from sqlalchemy import func, insert, select

from config import HEALTHY_FOODS_CSV, MASTER_NUTRITION_CSV, PROGRAMS_CSV, WORKOUT_CSV
from database.db_engine import SessionLocal
from database.db_models import DBHealthyFood, DBMasterNutrition, DBProgramSummary, DBWorkout


logger = logging.getLogger(__name__)


def _number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _nutrition_row(row):
    data = {"food_name": row["food_name"], "food_type": row.get("food_type"), "source": row.get("source")}
    for key in ("calories", "protein_g", "fat_g", "carbs_g", "fiber_g", "sugar_g", "sodium_mg", "health_score"):
        data[key] = _number(row.get(key))
    for key in ("contains_gluten", "contains_dairy", "contains_nuts", "contains_soy", "contains_eggs", "contains_fish"):
        data[key] = str(row.get(key, "")).strip().lower() in {"true", "1", "yes"}
    data["_food_name_lower"] = row["food_name"].lower()
    return data


def _program_row(row):
    length = row.get("program_length") or ""
    weeks = re.search(r"\d+(?:\.\d+)?", length)
    exercises = _number(row.get("total_exercises"))
    data = {key: row.get(key) for key in (
        "title", "description", "level", "goal", "equipment", "program_length",
        "time_per_workout", "created", "last_edit",
    )}
    data["total_exercises"] = int(exercises) if exercises is not None else None
    data["_weeks_num"] = int(float(weeks.group())) if weeks else None
    return data


def _workout_row(row):
    body_part = row.get("Body Part") or ""
    muscle = row.get("Type of Muscle") or ""
    return {
        "body_part": body_part,
        "type_of_muscle": muscle,
        "workout": row.get("Workout") or "",
        "sets": row.get("Sets") or "",
        "reps_per_set": row.get("Reps per Set") or "",
        "_body_part_lower": body_part.lower(),
        "_type_of_muscle_lower": muscle.lower(),
    }


def _healthy_food_row(row):
    data = {"food_name": row["food_name"], "food_type": row.get("food_type") or ""}
    for key in ("calories", "protein_g", "fat_g", "carbs_g", "fiber_g", "sugar_g", "sodium_mg", "health_score"):
        data[key] = _number(row.get(key)) or 0.0
    data["_food_name_lower"] = row["food_name"].lower()
    return data


def _seed_table(db_factory, model, path, convert):
    if not path.is_file():
        logger.warning("Katalog %s belum tersedia: %s", model.__tablename__, path)
        return 0

    with db_factory.begin() as db:
        if db.scalar(select(func.count()).select_from(model)):
            return 0

        total = 0
        batch = []
        with path.open(newline="", encoding="utf-8-sig") as source:
            for row in csv.DictReader(source):
                batch.append(convert(row))
                if len(batch) == 500:
                    db.execute(insert(model), batch)
                    total += len(batch)
                    batch.clear()
            if batch:
                db.execute(insert(model), batch)
                total += len(batch)

    logger.info("Katalog %s diisi: %d baris", model.__tablename__, total)
    return total


def seed_catalogs(
    db_factory=SessionLocal,
    nutrition_csv=MASTER_NUTRITION_CSV,
    programs_csv=PROGRAMS_CSV,
    workout_csv=WORKOUT_CSV,
    healthy_foods_csv=HEALTHY_FOODS_CSV,
):
    """Impor katalog yang dipakai halaman Nutrition, Workout, dan Workout Program."""
    return {
        "nutrition": _seed_table(db_factory, DBMasterNutrition, nutrition_csv, _nutrition_row),
        "programs": _seed_table(db_factory, DBProgramSummary, programs_csv, _program_row),
        "workouts": _seed_table(db_factory, DBWorkout, workout_csv, _workout_row),
        "healthy_foods": _seed_table(db_factory, DBHealthyFood, healthy_foods_csv, _healthy_food_row),
    }
