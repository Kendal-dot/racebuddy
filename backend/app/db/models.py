from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class TrainingPlan(Base):
    __tablename__ = "training_plans"
    
    id = Column(String, primary_key=True, index=True)
    
    # User data
    gender = Column(String, nullable=False)
    height_cm = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    fitness_level = Column(String, nullable=False)
    
    # Race data
    race = Column(String, nullable=False, default="lidingo")
    target_time = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    race_date = Column(Date, nullable=False)
    
    # Training preferences
    training_days_per_week = Column(Integer, default=4)
    previous_race_times = Column(JSON, default=list)
    injuries = Column(JSON, default=list)
    
    # Generated plan
    plan_data = Column(JSON, nullable=False)  # Stores the complete training plan
    total_weeks = Column(Integer, nullable=False)
    total_distance_km = Column(Float, nullable=False)
    
    # File paths
    ics_file_path = Column(String)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<TrainingPlan(id={self.id}, race={self.race}, target_time={self.target_time})>"