from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class FitnessLevelEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class RaceEnum(str, Enum):
    lidingo = "lidingo"

# Training Plan Request


class TrainingPlanRequest(BaseModel):
    # Användardata
    gender: GenderEnum
    height_cm: int = Field(..., ge=100, le=250,
                           description="Height in centimeters")
    weight_kg: float = Field(..., ge=30, le=200,
                             description="Weight in kilograms")
    age: int = Field(..., ge=12, le=100, description="Age in years")
    fitness_level: FitnessLevelEnum

    # Loppdata
    race: RaceEnum = RaceEnum.lidingo
    target_time: str = Field(..., description="Target time in HH:MM:SS format")
    start_date: date = Field(..., description="Training start date")
    race_date: date = Field(..., description="Race date")

    # Valbart
    previous_race_times: Optional[List[str]] = Field(
        default=[], description="Previous race times")
    injuries: Optional[List[str]] = Field(
        default=[], description="Current or recent injuries")
    training_days_per_week: Optional[int] = Field(default=4, ge=3, le=7)

    @validator('target_time')
    def validate_target_time(cls, v):
        try:
            # Validera HH:MM:SS format
            parts = v.split(':')
            if len(parts) != 3:
                raise ValueError
            hours, minutes, seconds = map(int, parts)
            if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
                raise ValueError
        except:
            raise ValueError('Target time must be in HH:MM:SS format')
        return v

    @validator('race_date')
    def validate_race_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('Race date must be after start date')
        return v

# Training Session


class TrainingSession(BaseModel):
    date: date
    type: str = Field(...,
                      description="Type of training (e.g., 'Easy run', 'Interval', 'Long run')")
    description: str = Field(...,
                             description="Detailed description of the session")
    distance_km: Optional[int] = Field(
        None, ge=0, description="Distance in kilometers")
    duration_minutes: Optional[int] = Field(
        None, ge=0, description="Duration in minutes")
    pace: Optional[str] = Field(
        None, description="Target pace (e.g., '5:30/km')")
    intensity: Optional[str] = Field(None, description="Intensity level")
    notes: Optional[str] = Field(None, description="Additional notes")

# Week Plan


class WeekPlan(BaseModel):
    week_number: int = Field(..., ge=1)
    start_date: date
    end_date: date
    focus: str = Field(...,
                       description="Week focus (e.g., 'Base building', 'Speed work')")
    total_distance_km: float = Field(..., ge=0)
    sessions: List[TrainingSession]

# Training Plan Response


class TrainingPlanResponse(BaseModel):
    id: str = Field(..., description="Unique plan identifier")
    user_data: TrainingPlanRequest
    weeks: List[WeekPlan]
    total_weeks: int
    total_distance_km: float
    ics_download_url: Optional[str] = Field(
        None, description="URL to download .ics calendar file")
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

# Race Info


class RaceInfo(BaseModel):
    race_id: str
    name: str
    distance_km: float
    location: str
    description: str
    elevation_gain_m: int
    typical_conditions: str
    key_challenges: List[str]

# Simple response models


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.now)


class TrainingPlan(BaseModel):
    weeks: List[Dict]
    total_weeks: int
    total_distance_km: int = Field(..., ge=0)
