"""
Router: /api/programs
"""
from fastapi import APIRouter, Query
from typing import Optional

from data_loader import search_programs
from models import APIResponse
from database.db_engine import SessionLocal
from database.db_models import DBProgramSummary
from sqlalchemy import func

router = APIRouter()


@router.get("")
async def list_programs(
    level: Optional[str] = Query(None, description="beginner | intermediate | advanced"),
    goal: Optional[str] = Query(None, description="muscle gain | weight loss | strength | endurance"),
    equipment: Optional[str] = Query(None, description="Full Gym | Garage Gym | Dumbbell Only"),
    max_weeks: Optional[int] = Query(None, description="Maksimal durasi program (minggu)"),
    q: Optional[str] = Query(None, description="Keyword search"),
    limit: int = Query(20, le=100),
):
    """Cari dan filter program latihan."""
    results = search_programs(
        level=level,
        goal=goal,
        equipment=equipment,
        max_weeks=max_weeks,
        query=q,
        limit=limit,
    )
    return APIResponse(success=True, data=results, total=len(results))


@router.get("/levels")
async def get_levels():
    """Daftar level yang tersedia."""
    with SessionLocal() as db:
        levels = db.query(DBProgramSummary.level).filter(DBProgramSummary.level.isnot(None)).distinct().all()
        return APIResponse(success=True, data=sorted([r[0] for r in levels if r[0]]))


@router.get("/goals")
async def get_goals():
    """Daftar goal yang tersedia."""
    with SessionLocal() as db:
        goals = db.query(DBProgramSummary.goal).filter(DBProgramSummary.goal.isnot(None)).distinct().all()
        return APIResponse(success=True, data=sorted([r[0] for r in goals if r[0]]))


@router.get("/equipment")
async def get_equipment_types():
    """Daftar equipment yang tersedia."""
    with SessionLocal() as db:
        equip = db.query(DBProgramSummary.equipment).filter(DBProgramSummary.equipment.isnot(None)).distinct().all()
        return APIResponse(success=True, data=sorted([r[0] for r in equip if r[0]]))


@router.get("/stats")
async def get_program_stats():
    """Statistik ringkasan dari program library."""
    with SessionLocal() as db:
        total = db.query(DBProgramSummary).count()
        if total == 0:
            return APIResponse(success=False, message="Dataset tidak tersedia")

        stats = {"total_programs": total}

        def get_top_10(column):
            res = db.query(column, func.count(column)).group_by(column).order_by(func.count(column).desc()).limit(10).all()
            return {r[0]: r[1] for r in res if r[0]}

        stats["by_level"] = get_top_10(DBProgramSummary.level)
        stats["by_goal"] = get_top_10(DBProgramSummary.goal)
        stats["by_equipment"] = get_top_10(DBProgramSummary.equipment)

        return APIResponse(success=True, data=stats)
