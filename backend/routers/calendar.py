"""
Router: /api/calendar
Endpoints untuk integrasi kalender (menghasilkan file .ics).
"""
import logging
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Annotated, List, Literal, Optional, Union

# icalendar sudah kita install di sesi sebelumnya
from icalendar import Calendar, Event, Alarm

from auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])

# Struktur mengikuti JSON plan dari AI Plan; field tambahan dari AI diabaikan
class CalendarExercise(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    sets: Union[int, Annotated[str, Field(max_length=20)], None] = Field(None, union_mode="left_to_right")
    reps: Union[int, Annotated[str, Field(max_length=50)], None] = Field(None, union_mode="left_to_right")
    notes: Optional[str] = Field(None, max_length=300)


class CalendarSession(BaseModel):
    day: Optional[str] = Field("Senin", max_length=50)
    focus: Optional[str] = Field(None, max_length=100)
    exercises: List[CalendarExercise] = Field(default_factory=list, max_length=30)


class CalendarFood(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    portion: Optional[str] = Field(None, max_length=50)
    calories: Union[int, float, Annotated[str, Field(max_length=20)], None] = Field(None, union_mode="left_to_right")


class CalendarMeal(BaseModel):
    meal_name: Optional[str] = Field(None, max_length=100)
    time: Optional[str] = Field(None, max_length=30)
    foods: List[CalendarFood] = Field(default_factory=list, max_length=30)


class SyncCalendarRequest(BaseModel):
    title: str = Field(..., max_length=100)
    plan_type: Literal["workout", "meal"]
    schedule: Optional[List[CalendarSession]] = Field(None, max_length=14)
    meals: Optional[List[CalendarMeal]] = Field(None, max_length=20)


def _parse_time(value: Optional[str]) -> tuple[int, int]:
    """Ubah "08:00" menjadi (8, 0); nilai yang tidak valid memakai jam 08:00."""
    try:
        hour, minute = map(int, (value or "").strip().split(":")[:2])
    except ValueError:
        return 8, 0
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return 8, 0

def get_next_weekday(target_weekday: int, hour: int = 7) -> datetime:
    """Mendapatkan datetime untuk hari tertentu di minggu ini/depan.
    target_weekday: 0=Senin, 1=Selasa, dst.
    """
    today = date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0: # Jika hari sudah lewat minggu ini, jadwalkan untuk minggu depan
        days_ahead += 7
    target_date = today + timedelta(days=days_ahead)
    return datetime.combine(target_date, datetime.min.time()).replace(hour=hour)

DAY_MAP = {
    "senin": 0, "selasa": 1, "rabu": 2,
    "kamis": 3, "jumat": 4, "sabtu": 5, "minggu": 6
}

@router.post("/export")
def export_to_calendar(plan: SyncCalendarRequest):
    """
    Convert workout/meal plan JSON → .ics calendar file.
    Menerima JSON plan dari frontend.
    """
    cal = Calendar()
    cal.add('prodid', '-//FitMind AI//Plan Generator//ID')
    cal.add('version', '2.0')

    # Jika ini WORKOUT plan
    if plan.plan_type == "workout" and plan.schedule:
        for session in plan.schedule:
            event = Event()

            # Parsing hari menjadi integer (0-6)
            day_str = (session.day or "Senin").strip().lower()
            weekday_idx = DAY_MAP.get(day_str, 0)

            # Set waktu latihan (default jam 07:00 pagi selama 1 jam)
            dt_start = get_next_weekday(weekday_idx, hour=7)
            dt_end = dt_start + timedelta(hours=1)

            focus = session.focus or "Workout"
            event.add('summary', f"🏋️ FitMind: {focus}")

            # Format deskripsi gerakan
            desc_lines = [f"Program: {plan.title}", f"Fokus: {focus}", ""]
            for ex in session.exercises:
                desc_lines.append(f"• {ex.name} — {ex.sets}x{ex.reps}")
                if ex.notes:
                    desc_lines.append(f"  Note: {ex.notes}")

            event.add('description', "\n".join(desc_lines))
            event.add('dtstart', dt_start)
            event.add('dtend', dt_end)

            # Alarm 1 jam sebelumnya
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f"Reminder Latihan: {focus}")
            alarm.add('trigger', timedelta(hours=-1))
            event.add_component(alarm)
            
            cal.add_component(event)

    # Jika ini MEAL plan (Opsional: jadwalkan prep meals / sarapan dsb)
    elif plan.plan_type == "meal" and plan.meals:
        # Jadwalkan untuk BESOK
        tomorrow = date.today() + timedelta(days=1)
        for meal in plan.meals:
            event = Event()
            
            # Parse waktu (misal "08:00")
            time_str = meal.time or "08:00"
            hour, minute = _parse_time(time_str)

            dt_start = datetime.combine(tomorrow, datetime.min.time()).replace(hour=hour, minute=minute)
            dt_end = dt_start + timedelta(minutes=30)

            event.add('summary', f"🥗 FitMind: {meal.meal_name or 'Meal'}")

            desc_lines = [f"Program: {plan.title}", f"Waktu: {time_str}", ""]
            for food in meal.foods:
                desc_lines.append(f"• {food.name} ({food.portion}) — {food.calories} kkal")
            
            event.add('description', "\n".join(desc_lines))
            event.add('dtstart', dt_start)
            event.add('dtend', dt_end)
            
            cal.add_component(event)
    
    else:
        raise HTTPException(status_code=400, detail="Data plan tidak valid atau tidak memiliki schedule/meals.")

    # Kembalikan sebagai file biner .ics
    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=fitmind_{plan.plan_type}.ics"}
    )
