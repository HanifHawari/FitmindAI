"""
FitMind AI - Data Loader (Migrated to SQL)
Fungsi pencarian menggunakan SQLAlchemy untuk membaca database yang dikonfigurasi.
"""
from sqlalchemy import or_

from database.db_engine import SessionLocal
from database.db_models import (
    DBWorkout, DBMasterNutrition, DBProgramSummary
)

# ==============================================================
# Query Helpers
# ==============================================================

def search_workout(body_part: str = None, muscle: str = None) -> list[dict]:
    with SessionLocal() as db:
        query = db.query(DBWorkout)
        if body_part:
            query = query.filter(DBWorkout._body_part_lower.ilike(f"%{body_part.lower()}%"))
        if muscle:
            query = query.filter(DBWorkout._type_of_muscle_lower.ilike(f"%{muscle.lower()}%"))
        
        results = query.all()
        return [{
            "Body Part": r.body_part,
            "Type of Muscle": r.type_of_muscle,
            "Workout": r.workout,
            "Sets": r.sets,
            "Reps per Set": r.reps_per_set
        } for r in results]


def search_foods(
    query: str = None,
    max_calories: float = None,
    min_health_score: float = None,
    food_type: str = None,
    limit: int = 20
) -> list[dict]:
    with SessionLocal() as db:
        q = db.query(DBMasterNutrition)
        
        if query:
            q = q.filter(DBMasterNutrition._food_name_lower.ilike(f"%{query.lower()}%"))
        
        if max_calories is not None:
            q = q.filter(DBMasterNutrition.calories <= max_calories)
            
        if min_health_score is not None:
            q = q.filter(DBMasterNutrition.health_score >= min_health_score)
            
        if food_type:
            q = q.filter(DBMasterNutrition.food_type.ilike(f"%{food_type}%"))
            
        results = q.limit(limit).all()
        
        return [{
            "food_name": r.food_name,
            "calories": r.calories,
            "protein_g": r.protein_g,
            "fat_g": r.fat_g,
            "carbs_g": r.carbs_g,
            "fiber_g": r.fiber_g,
            "sugar_g": r.sugar_g,
            "sodium_mg": r.sodium_mg,
            "health_score": r.health_score,
            "food_type": r.food_type,
            "source": r.source,
            "contains_gluten": r.contains_gluten,
            "contains_dairy": r.contains_dairy,
            "contains_nuts": r.contains_nuts,
            "contains_soy": r.contains_soy,
            "contains_eggs": r.contains_eggs,
            "contains_fish": r.contains_fish
        } for r in results]


def search_foods_allergen_free(
    query: str = None,
    exclude_gluten: bool = False,
    exclude_dairy: bool = False,
    exclude_nuts: bool = False,
    exclude_soy: bool = False,
    exclude_eggs: bool = False,
    exclude_fish: bool = False,
    limit: int = 20
) -> list[dict]:
    with SessionLocal() as db:
        q = db.query(DBMasterNutrition)
        
        if exclude_gluten:
            q = q.filter(DBMasterNutrition.contains_gluten == False)
        if exclude_dairy:
            q = q.filter(DBMasterNutrition.contains_dairy == False)
        if exclude_nuts:
            q = q.filter(DBMasterNutrition.contains_nuts == False)
        if exclude_soy:
            q = q.filter(DBMasterNutrition.contains_soy == False)
        if exclude_eggs:
            q = q.filter(DBMasterNutrition.contains_eggs == False)
        if exclude_fish:
            q = q.filter(DBMasterNutrition.contains_fish == False)
            
        if query:
            q = q.filter(DBMasterNutrition._food_name_lower.ilike(f"%{query.lower()}%"))
            
        results = q.limit(limit).all()
        
        return [{
            "food_name": r.food_name,
            "calories": r.calories,
            "protein_g": r.protein_g,
            "fat_g": r.fat_g,
            "carbs_g": r.carbs_g,
            "fiber_g": r.fiber_g,
            "sugar_g": r.sugar_g,
            "sodium_mg": r.sodium_mg,
            "health_score": r.health_score,
            "food_type": r.food_type,
            "source": r.source,
            "contains_gluten": r.contains_gluten,
            "contains_dairy": r.contains_dairy,
            "contains_nuts": r.contains_nuts,
            "contains_soy": r.contains_soy,
            "contains_eggs": r.contains_eggs,
            "contains_fish": r.contains_fish
        } for r in results]


def search_programs(
    level: str = None,
    goal: str = None,
    equipment: str = None,
    max_weeks: int = None,
    query: str = None,
    limit: int = 20
) -> list[dict]:
    with SessionLocal() as db:
        q = db.query(DBProgramSummary)
        
        if level and level.lower() == "beginner":
            q = q.filter(or_(
                DBProgramSummary.level.ilike("%Beginner%"),
                DBProgramSummary.level.ilike("%Novice%"),
            ))
        elif level:
            q = q.filter(DBProgramSummary.level.ilike(f"%{level}%"))
        if goal:
            q = q.filter(DBProgramSummary.goal.ilike(f"%{goal}%"))
        if equipment:
            q = q.filter(DBProgramSummary.equipment.ilike(f"%{equipment}%"))
        if max_weeks:
            q = q.filter(DBProgramSummary._weeks_num <= max_weeks)
        if query:
            q_str = f"%{query.lower()}%"
            q = q.filter(
                or_(
                    DBProgramSummary.title.ilike(q_str),
                    DBProgramSummary.description.ilike(q_str)
                )
            )
            
        results = q.limit(limit).all()
        
        return [{
            "title": r.title,
            "description": r.description,
            "level": r.level,
            "goal": r.goal,
            "equipment": r.equipment,
            "program_length": r.program_length,
            "time_per_workout": r.time_per_workout,
            "total_exercises": r.total_exercises,
            "created": r.created,
            "last_edit": r.last_edit
        } for r in results]


def get_user_stats_summary() -> dict:
    """Fallback statistik (bisa diquery dari Supabase jika mau)."""
    return {
        "total_members": 973,
        "avg_bmi": 26.5,
        "avg_calories_burned": 890.0,
        "avg_session_duration": 1.2,
        "workout_types": {"Cardio": 300, "Strength": 400},
        "experience_distribution": {"Beginner": 200, "Intermediate": 500}
    }
