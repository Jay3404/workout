from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal # Numeric(Decimal) 타입 처리를 위해

# --- Exercise Schemas ---
class ExerciseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    target_part: str = Field(..., min_length=1, max_length=50)

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase): # DB에서 읽어올 때 사용 (응답 모델)
    id: int

    class Config:
        orm_mode = True # SQLAlchemy 모델과 호환되도록 설정 (FastAPI 0.x)
        # from_attributes = True # Pydantic v2+

# --- WorkoutLog Schemas ---
class WorkoutLogBase(BaseModel):
    date: date
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=2) # ge=0 (0 이상)
    reps: Optional[int] = Field(None, ge=0)
    sets: Optional[int] = Field(None, ge=0)

class WorkoutLogCreate(WorkoutLogBase):
    exercise_id: int

class WorkoutLog(WorkoutLogBase): # DB에서 읽어올 때 사용 (응답 모델)
    id: int
    exercise_id: int
    # exercise: Optional[Exercise] = None # 필요하다면 관계 로드

    class Config:
        orm_mode = True # SQLAlchemy 모델과 호환되도록 설정
        # from_attributes = True # Pydantic v2+

# --- Request Body Schemas for API ---
class BodyPartRequest(BaseModel):
    body_part: str

class ExerciseHistoryRequest(BaseModel):
    exercise_id: int

# --- Response Schemas for API ---
class ExerciseListResponse(BaseModel):
    exercises: List[Exercise]

class ExerciseHistoryDetail(WorkoutLog): # WorkoutLog를 그대로 사용하거나 확장
    pass

class ExerciseHistoryResponse(BaseModel):
    exercise_name: str
    history: List[ExerciseHistoryDetail]

class MessageResponse(BaseModel):
    message: str