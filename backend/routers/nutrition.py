"""
Router: /api/nutrition
"""
from fastapi import APIRouter, Query
from typing import Optional

from data_loader import search_foods, search_foods_allergen_free
from models import APIResponse

router = APIRouter()


@router.get("/search")
def search_food(
    q: Optional[str] = Query(None, max_length=100, description="Nama makanan"),
    max_calories: Optional[float] = Query(None, description="Maksimal kalori per 100g"),
    min_health_score: Optional[float] = Query(None, description="Minimal health score (0-100)"),
    food_type: Optional[str] = Query(None, max_length=50, description="Tipe makanan"),
    no_gluten: bool = Query(False),
    no_dairy: bool = Query(False),
    no_nuts: bool = Query(False),
    no_soy: bool = Query(False),
    no_eggs: bool = Query(False),
    no_fish: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Cari makanan dengan filter nutrisi dan alergen.
    Menggabungkan data dari foods_usda + health_scores datasets.
    """
    # Jika ada filter alergen, gunakan health_scores dataset
    has_allergen_filter = any([no_gluten, no_dairy, no_nuts, no_soy, no_eggs, no_fish])

    if has_allergen_filter:
        results = search_foods_allergen_free(
            query=q,
            exclude_gluten=no_gluten,
            exclude_dairy=no_dairy,
            exclude_nuts=no_nuts,
            exclude_soy=no_soy,
            exclude_eggs=no_eggs,
            exclude_fish=no_fish,
            limit=limit,
        )
    else:
        results = search_foods(
            query=q,
            max_calories=max_calories,
            min_health_score=min_health_score,
            food_type=food_type,
            limit=limit,
        )

    return APIResponse(success=True, data=results, total=len(results))


from database.db_engine import SessionLocal
from database.db_models import DBMasterNutrition

@router.get("/healthy")
def get_healthy_foods(
    food_type: Optional[str] = Query(None, max_length=50, description="Tipe: Vegetable, Fruit, Protein, dll"),
    min_score: float = Query(60, description="Minimal health score"),
    limit: int = Query(20, ge=1, le=100),
):
    """Ambil makanan sehat dari database."""
    with SessionLocal() as db:
        q = db.query(DBMasterNutrition).filter(DBMasterNutrition.health_score >= min_score)
        
        if food_type:
            q = q.filter(DBMasterNutrition.food_type.ilike(f"%{food_type}%"))
            
        results = q.order_by(DBMasterNutrition.health_score.desc()).limit(limit).all()
        
        data = [{
            "food_name": r.food_name,
            "calories": r.calories,
            "protein_g": r.protein_g,
            "fat_g": r.fat_g,
            "carbs_g": r.carbs_g,
            "health_score": r.health_score,
            "food_type": r.food_type,
            "source": r.source
        } for r in results]
        
        return APIResponse(success=True, data=data, total=len(data))


@router.get("/food-types")
def get_food_types():
    """Daftar unique food types dari dataset."""
    with SessionLocal() as db:
        results = db.query(DBMasterNutrition.food_type).distinct().all()
        types = [r[0] for r in results if r[0]]
        return APIResponse(success=True, data=sorted(types), total=len(types))


@router.get("/meal-plan")
def generate_meal_plan(
    target_calories: int = Query(2000, ge=500, le=10000, description="Target kalori harian"),
    diet_type: Optional[str] = Query(None, max_length=30, description="vegan | vegetarian | keto"),
    no_gluten: bool = Query(False),
    no_dairy: bool = Query(False),
):
    """
    Generate meal plan sederhana berdasarkan target kalori menggunakan SQL.
    Dibagi: Breakfast 25%, Lunch 35%, Dinner 30%, Snack 10%.
    """
    with SessionLocal() as db:
        q = db.query(DBMasterNutrition).filter(DBMasterNutrition.calories > 0)
        
        if diet_type:
            q = q.filter(DBMasterNutrition.food_type.ilike(f"%{diet_type}%"))
            
        if no_gluten:
            q = q.filter(DBMasterNutrition.contains_gluten == False)
        if no_dairy:
            q = q.filter(DBMasterNutrition.contains_dairy == False)
            
        # Ambil top 200 makanan tershat yang kalorinya tidak lebih besar dari 1.5x porsi maksimal (sekitar 1000 kal)
        available = q.filter(DBMasterNutrition.calories <= target_calories * 0.5)\
                     .order_by(DBMasterNutrition.health_score.desc()).limit(200).all()
                     
        if not available:
            return APIResponse(success=False, message="Tidak ada makanan yang cocok dengan kriteria")

        import random
        def pick_foods(target_cal: float, n: int = 3) -> list[dict]:
            picked = []
            if not available:
                return picked
            
            # Filter makanan yang masuk akal untuk porsi ini
            valid_foods = [f for f in available if f.calories > 0 and f.calories <= target_cal]
            if not valid_foods:
                valid_foods = available
                
            shuffled = random.sample(valid_foods, min(len(valid_foods), n * 4))
            
            current_cal = 0
            for item in shuffled:
                if len(picked) < n and current_cal + item.calories <= target_cal * 1.2:
                    picked.append({
                        "food_name": item.food_name,
                        "calories": item.calories,
                        "protein_g": item.protein_g,
                        "health_score": item.health_score
                    })
                    current_cal += item.calories
                    
            # Fallback jika terlalu strict
            if not picked:
                for item in valid_foods[:n]:
                    picked.append({
                        "food_name": item.food_name,
                        "calories": item.calories,
                        "protein_g": item.protein_g,
                        "health_score": item.health_score
                    })
            return picked

        meal_plan = {
            "target_calories": target_calories,
            "breakdown": {
                "Breakfast": {
                    "target_kcal": int(target_calories * 0.25),
                    "foods": pick_foods(target_calories * 0.25 / 3),
                },
                "Lunch": {
                    "target_kcal": int(target_calories * 0.35),
                    "foods": pick_foods(target_calories * 0.35 / 3),
                },
                "Dinner": {
                    "target_kcal": int(target_calories * 0.30),
                    "foods": pick_foods(target_calories * 0.30 / 3),
                },
                "Snack": {
                    "target_kcal": int(target_calories * 0.10),
                    "foods": pick_foods(target_calories * 0.10 / 2, n=2),
                },
            }
        }
        return APIResponse(success=True, data=meal_plan)


@router.get("/nutriscore-stats")
def get_nutriscore_distribution():
    """Distribusi health score dari dataset makanan sehat menggunakan SQL."""
    with SessionLocal() as db:
        # Menghitung secara efisien dengan kondisi SQL
        # Excellent (80+), Good (60-79), Fair (40-59), Poor (<40)
        from sqlalchemy import case, func
        
        score_case = case(
            (DBMasterNutrition.health_score >= 80, "Excellent"),
            (DBMasterNutrition.health_score >= 60, "Good"),
            (DBMasterNutrition.health_score >= 40, "Fair"),
            else_="Poor"
        )
        
        results = db.query(score_case.label("category"), func.count().label("count"))\
                    .group_by(score_case).all()
                    
        dist = {r.category: r.count for r in results}
        
        return APIResponse(success=True, data=dist)
