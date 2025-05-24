from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import TrainingPlan
from core.ics_utils import generate_ics_file
import io
import os
from datetime import datetime

router = APIRouter()


@router.get("/plans/{plan_id}/export/ics")
async def export_training_plan_ics(plan_id: str, db: Session = Depends(get_db)):
    """Export training plan as .ics calendar file"""

    # Get training plan
    db_plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()

    if not db_plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    try:
        # Generate ICS content
        ics_content = generate_ics_file(
            plan_data=db_plan.plan_data,
            plan_id=plan_id,
            race_name=db_plan.race.title() + "löppet",
            race_date=db_plan.race_date
        )

        # Create file stream
        ics_file = io.BytesIO(ics_content.encode('utf-8'))

        # Generate filename
        filename = f"training_plan_{db_plan.race}_{plan_id[:8]}.ics"

        return StreamingResponse(
            ics_file,
            media_type="text/calendar",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate calendar file: {str(e)}"
        )


@router.get("/plans/{plan_id}/export/json")
async def export_training_plan_json(plan_id: str, db: Session = Depends(get_db)):
    """Export training plan as JSON"""

    db_plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()

    if not db_plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    # Return plan data
    export_data = {
        "plan_id": db_plan.id,
        "created_at": db_plan.created_at.isoformat(),
        "race": db_plan.race,
        "target_time": db_plan.target_time,
        "race_date": db_plan.race_date.isoformat(),
        "user_info": {
            "fitness_level": db_plan.fitness_level,
            "gender": db_plan.gender,
            "age": db_plan.age
        },
        "plan_summary": {
            "total_weeks": db_plan.total_weeks,
            "total_distance_km": db_plan.total_distance_km,
            "training_days_per_week": db_plan.training_days_per_week
        },
        "training_plan": db_plan.plan_data
    }

    return export_data


@router.get("/plans/{plan_id}/summary")
async def get_plan_summary(plan_id: str, db: Session = Depends(get_db)):
    """Get training plan summary"""

    db_plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()

    if not db_plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    # Calculate statistics from plan data
    weeks_data = db_plan.plan_data.get("weeks", [])

    # Count training types
    session_types = {}
    total_sessions = 0

    for week in weeks_data:
        for session in week.get("sessions", []):
            session_type = session.get("type", "Unknown")
            session_types[session_type] = session_types.get(
                session_type, 0) + 1
            total_sessions += 1

    # Calculate distance distribution per week
    weekly_distances = []
    for week in weeks_data:
        weekly_distances.append({
            "week": week.get("week_number"),
            "distance": week.get("total_distance_km"),
            "focus": week.get("focus")
        })

    summary = {
        "plan_id": db_plan.id,
        "overview": {
            "total_weeks": db_plan.total_weeks,
            "total_distance_km": int(db_plan.total_distance_km),
            "total_sessions": total_sessions,
            "avg_sessions_per_week": round(total_sessions / max(db_plan.total_weeks, 1), 1),
            "avg_distance_per_week": int(round(db_plan.total_distance_km / max(db_plan.total_weeks, 1)))
        },
        "session_distribution": session_types,
        "weekly_progression": [{
            "week": week.get("week_number"),
            "distance": int(week.get("total_distance_km")),
            "focus": week.get("focus")
        } for week in weekly_distances],
        "key_dates": {
            "training_start": db_plan.start_date.isoformat(),
            "race_date": db_plan.race_date.isoformat(),
            "created": db_plan.created_at.isoformat()
        }
    }

    return summary
