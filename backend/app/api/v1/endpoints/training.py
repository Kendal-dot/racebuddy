from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
from datetime import datetime, date
import logging
import json

from core.schemas import (
    TrainingPlanRequest,
    TrainingPlanResponse,
    MessageResponse
)
from core.training_logic import ai_training_generator, training_generator
from db.session import get_db
from db.models import TrainingPlan

router = APIRouter()


def serialize_plan_data(plan_data):
    """Converts Pydantic objects to JSON-serializable data"""
    def convert_obj(obj):
        if isinstance(obj, date):  # Handle date objects
            return obj.isoformat()
        elif isinstance(obj, datetime):  # Handle datetime objects
            return obj.isoformat()
        elif hasattr(obj, 'dict'):  # Pydantic model
            return convert_obj(obj.dict())
        elif hasattr(obj, '__dict__'):
            return {key: convert_obj(value) for key, value in obj.__dict__.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_obj(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_obj(value) for key, value in obj.items()}
        else:
            return obj

    return convert_obj(plan_data)


@router.post("/generate-ai-plan")
async def generate_ai_training_plan(request: TrainingPlanRequest):
    """
    New endpoint: Generate AI training plan directly without saving to database
    Returns structured data that can be used for calendar view and .ics export
    """
    try:
        logging.info("Generating AI-enhanced training plan...")

        # Use AI-enhanced generator
        plan_data = ai_training_generator.generate_plan(request)

        # Format for calendar view (same format as in the image)
        calendar_sessions = []

        for week in plan_data["weeks"]:
            for session in week.sessions:
                # Format as in calendar image
                calendar_session = {
                    "date": session.date.isoformat(),
                    "day_name": session.date.strftime("%A").upper(),
                    # "4 JUNE"
                    "day_date": session.date.strftime("%-d %B").upper(),
                    "pass": session.description,  # This becomes the title in the calendar
                    # This becomes the description
                    "fokus": session.notes or f"Träning för {request.race.value}",
                    "time_start": "11:00",  # Standard time
                    "time_end": "12:00",
                    "distance_km": session.distance_km,
                    "pace": session.pace,
                    "type": session.type,
                    "intensity": session.intensity,
                    "week_number": week.week_number,
                    "week_focus": week.focus
                }
                calendar_sessions.append(calendar_session)

        # Response structure
        response = {
            "success": True,
            "user_data": {
                "gender": request.gender.value,
                "age": request.age,
                "fitness_level": request.fitness_level.value,
                "target_time": request.target_time,
                "race": request.race.value,
                "training_days_per_week": request.training_days_per_week
            },
            "plan_summary": {
                "total_weeks": plan_data["total_weeks"],
                "total_distance_km": plan_data["total_distance_km"],
                "start_date": request.start_date.isoformat(),
                "race_date": request.race_date.isoformat()
            },
            "calendar_sessions": calendar_sessions,  # For calendar view
            "raw_plan_data": plan_data,  # For .ics export
            "generated_at": datetime.now().isoformat()
        }

        logging.info(
            f"AI training plan generated successfully with {len(calendar_sessions)} sessions")
        return response

    except Exception as e:
        logging.error(f"Error generating AI training plan: {str(e)}")

        # Fallback to standard generator
        try:
            logging.info("Falling back to standard training plan generator...")
            plan_data = training_generator.generate_plan(request)

            # Same formatting for fallback
            calendar_sessions = []
            for week in plan_data["weeks"]:
                for session in week.sessions:
                    calendar_session = {
                        "date": session.date.isoformat(),
                        "day_name": session.date.strftime("%A").upper(),
                        "day_date": session.date.strftime("%-d %B").upper(),
                        "pass": session.description,
                        "fokus": session.notes or f"Träning för {request.race.value}",
                        "time_start": "11:00",
                        "time_end": "12:00",
                        "distance_km": session.distance_km,
                        "pace": session.pace,
                        "type": session.type,
                        "intensity": session.intensity,
                        "week_number": week.week_number,
                        "week_focus": week.focus
                    }
                    calendar_sessions.append(calendar_session)

            return {
                "success": True,
                "fallback_used": True,
                "user_data": {
                    "gender": request.gender.value,
                    "age": request.age,
                    "fitness_level": request.fitness_level.value,
                    "target_time": request.target_time,
                    "race": request.race.value,
                    "training_days_per_week": request.training_days_per_week
                },
                "plan_summary": {
                    "total_weeks": plan_data["total_weeks"],
                    "total_distance_km": plan_data["total_distance_km"],
                    "start_date": request.start_date.isoformat(),
                    "race_date": request.race_date.isoformat()
                },
                "calendar_sessions": calendar_sessions,
                "raw_plan_data": plan_data,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as fallback_error:
            logging.error(
                f"Fallback training plan also failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Both AI and fallback training plan generation failed: {str(e)} | {str(fallback_error)}"
            )


@router.post("/generate-ics")
async def generate_ics_from_plan_data(plan_data: Dict[str, Any]):
    """
    Generate .ics file from plan data
    """
    try:
        from core.ics_utils import generate_ics_file

        # Extract info from plan data
        race_name = plan_data.get("user_data", {}).get("race", "Lidingöloppet")
        race_date = datetime.fromisoformat(
            plan_data.get("plan_summary", {}).get("race_date"))

        # Generate ICS content
        ics_content = generate_ics_file(
            plan_data=plan_data.get("raw_plan_data", {}),
            plan_id=str(uuid.uuid4()),
            race_name=race_name,
            race_date=race_date
        )

        return {
            "success": True,
            "ics_content": ics_content,
            "filename": f"training_plan_{race_name}_{datetime.now().strftime('%Y%m%d')}.ics"
        }

    except Exception as e:
        logging.error(f"Error generating ICS file: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate ICS file: {str(e)}")


@router.post("/plans", response_model=TrainingPlanResponse)
async def create_training_plan(
    request: TrainingPlanRequest,
    db: Session = Depends(get_db)
):
    """Create a new AI-enhanced training plan AND save to database"""
    try:
        # Try first with AI-enhanced generator
        try:
            logging.info("Generating AI-enhanced training plan...")
            plan_data = ai_training_generator.generate_plan(request)
            logging.info("AI-enhanced training plan generated successfully")
        except Exception as ai_error:
            logging.warning(
                f"AI training plan failed, using fallback: {ai_error}")
            # Fallback to standard generator if AI fails
            plan_data = training_generator.generate_plan(request)

        # Convert to JSON-serializable data
        serializable_plan_data = serialize_plan_data(plan_data)

        # Create unique ID
        plan_id = str(uuid.uuid4())

        # Save to database
        db_plan = TrainingPlan(
            id=plan_id,
            gender=request.gender.value,
            height_cm=request.height_cm,
            weight_kg=request.weight_kg,
            age=request.age,
            fitness_level=request.fitness_level.value,
            race=request.race.value,
            target_time=request.target_time,
            start_date=request.start_date,
            race_date=request.race_date,
            training_days_per_week=request.training_days_per_week,
            previous_race_times=request.previous_race_times,
            injuries=request.injuries,
            plan_data=serializable_plan_data,  # Use serialized data
            total_weeks=plan_data["total_weeks"],
            total_distance_km=plan_data["total_distance_km"]
        )

        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)

        # Convert back for response
        response = TrainingPlanResponse(
            id=plan_id,
            user_data=request,
            weeks=plan_data["weeks"],  # Use original data for response
            total_weeks=plan_data["total_weeks"],
            total_distance_km=plan_data["total_distance_km"],
            ics_download_url=f"/v1/calendar/plans/{plan_id}/export/ics",
            created_at=datetime.now()
        )

        logging.info(f"Training plan created successfully: {plan_id}")
        return response

    except Exception as e:
        logging.error(f"Error creating training plan: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create training plan: {str(e)}")


@router.get("/plans/{plan_id}", response_model=TrainingPlanResponse)
async def get_training_plan(plan_id: str, db: Session = Depends(get_db)):
    """Get a specific training plan"""

    db_plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()

    if not db_plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    try:
        # Reconstruct request object
        user_data = TrainingPlanRequest(
            gender=db_plan.gender,
            height_cm=db_plan.height_cm,
            weight_kg=db_plan.weight_kg,
            age=db_plan.age,
            fitness_level=db_plan.fitness_level,
            race=db_plan.race,
            target_time=db_plan.target_time,
            start_date=db_plan.start_date,
            race_date=db_plan.race_date,
            training_days_per_week=db_plan.training_days_per_week,
            previous_race_times=db_plan.previous_race_times or [],
            injuries=db_plan.injuries or []
        )

        response = TrainingPlanResponse(
            id=db_plan.id,
            user_data=user_data,
            weeks=db_plan.plan_data["weeks"],
            total_weeks=db_plan.total_weeks,
            total_distance_km=int(db_plan.total_distance_km),
            ics_download_url=f"/v1/calendar/plans/{plan_id}/export/ics",
            created_at=db_plan.created_at
        )

        return response

    except Exception as e:
        logging.error(f"Error retrieving training plan {plan_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve training plan")


@router.get("/plans", response_model=List[dict])
async def list_training_plans(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List training plans (for admin/debug)"""

    plans = db.query(TrainingPlan).offset(offset).limit(limit).all()

    result = []
    for plan in plans:
        result.append({
            "id": plan.id,
            "race": plan.race,
            "target_time": plan.target_time,
            "fitness_level": plan.fitness_level,
            "total_weeks": plan.total_weeks,
            "total_distance_km": plan.total_distance_km,
            "created_at": plan.created_at.isoformat()
        })

    return result


@router.delete("/plans/{plan_id}", response_model=MessageResponse)
async def delete_training_plan(plan_id: str, db: Session = Depends(get_db)):
    """Delete a training plan"""

    db_plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()

    if not db_plan:
        raise HTTPException(status_code=404, detail="Training plan not found")

    try:
        db.delete(db_plan)
        db.commit()

        return MessageResponse(message=f"Training plan {plan_id} deleted successfully")

    except Exception as e:
        logging.error(f"Error deleting training plan {plan_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to delete training plan")
