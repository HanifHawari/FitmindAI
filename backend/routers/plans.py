"""
Router: /api/plans
Endpoints untuk generate workout / meal plan terstruktur (JSON Mode).

Endpoint:
  POST /api/plans/generate  → Generate structured plan via LLM JSON Mode
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from models import PlanGenerateRequest, APIResponse
from agents.planner_agent import PlannerAgent

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])

# Singleton planner agent
_planner = PlannerAgent()


@router.post("/generate")
async def generate_plan(request: PlanGenerateRequest):
    """
    Generate workout atau meal plan terstruktur menggunakan LLM JSON Mode.

    Input: plan_type, goal, level, days_per_week, equipment, dll.
    Output: JSON terstruktur yang bisa di-render sebagai kartu visual,
            di-export ke .ics, atau dikirim ke WhatsApp.
    """
    plan_type = request.plan_type or "workout"

    # Bangun pesan instruksi dari parameter user
    if plan_type == "meal":
        instruction = (
            f"Buatkan meal plan harian dengan target kalori yang sesuai.\n"
            f"Goal: {request.goal or 'sehat umum'}\n"
            f"Diet: {request.diet_type or 'normal'}\n"
        )
        if request.allergies:
            instruction += f"Alergi/pantangan: {', '.join(request.allergies)}\n"
        if request.notes:
            instruction += f"Catatan tambahan: {request.notes}\n"
    else:
        instruction = (
            f"Buatkan program latihan gym.\n"
            f"Goal: {request.goal or 'general fitness'}\n"
            f"Level: {request.level or 'beginner'}\n"
            f"Hari per minggu: {request.days_per_week or 3}\n"
            f"Equipment: {request.equipment or 'Full Gym'}\n"
        )
        if request.notes:
            instruction += f"Catatan tambahan: {request.notes}\n"

    # Bangun profil user untuk konteks RAG
    user_profile = {}
    if request.goal:
        user_profile["goal"] = request.goal
    if request.level:
        user_profile["experience_level"] = request.level
    if request.equipment:
        user_profile["equipment"] = request.equipment

    # Ambil konteks dari dataset
    context = _planner.build_context(instruction, user_profile or None)

    # Pilih schema dan prompt sesuai plan_type
    schema = _planner.get_schema(plan_type)
    prompt = _planner.get_prompt(plan_type)

    try:
        result = await _planner.generate_structured(
            message=instruction,
            chat_history=[],
            context=context,
            response_schema=schema,
            system_prompt_override=prompt,
        )
    except Exception as e:
        logger.error(f"[Plans] Error generating plan: {e}")
        raise HTTPException(status_code=500, detail="Gagal membuat rencana. Silakan coba lagi.")

    # generate_structured mengembalikan {} saat LLM gagal atau JSON-nya tidak valid
    if not isinstance(result, dict) or not result:
        raise HTTPException(status_code=502, detail="Gagal membuat rencana. Silakan coba lagi.")
    logger.info(f"[Plans] Generated {plan_type} plan: {result.get('title', 'untitled')}")
    return APIResponse(success=True, data=result)
