from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base # 변경된 부분s

class Exercise(Base):
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    target_part = Column(String(50), nullable=False, index=True)

    logs = relationship('WorkoutLog', back_populates='exercise') # back_populates 사용

    def __repr__(self):
        return f"<Exercise {self.name} ({self.target_part})>"

class WorkoutLog(Base):
    __tablename__ = 'workout_logs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    weight = Column(Numeric(5, 2))
    reps = Column(Integer)
    sets = Column(Integer)

    exercise = relationship('Exercise', back_populates='logs') # back_populates 사용

    def __repr__(self):
        return f"<WorkoutLog {self.exercise_id} on {self.date}: {self.weight}kg>"