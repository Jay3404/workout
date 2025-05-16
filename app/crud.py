from typing import List, Optional

from sqlalchemy.orm import Session
from . import models, schemas
import csv
import os
from datetime import date

def get_exercise_by_name(db: Session, name: str):
    return db.query(models.Exercise).filter(models.Exercise.name == name).first()

def create_exercise(db: Session, exercise: schemas.ExerciseCreate):
    db_exercise = models.Exercise(name=exercise.name, target_part=exercise.target_part)
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

def get_distinct_target_parts(db: Session) -> List[str]:
    print("--- Inside get_distinct_target_parts ---") # 함수 호출 확인용
    try:
        # SQLAlchemy 쿼리가 실제로 어떤 결과를 반환하는지 확인
        results = db.query(models.Exercise.target_part).distinct().all()
        print(db.query(models.Exercise.target_part))
        print(f"★★★ Raw distinct target_part results from DB query: {results} ★★★") # <--- 이 로그가 중요합니다!

        parts = sorted([result[0] for result in results if result[0] is not None])
        print(f"Processed parts list for dropdown: {parts}") # 최종 처리된 리스트
        return parts
    except Exception as e:
        print(f"Error in get_distinct_target_parts: {e}")
        return []
def get_exercises_by_target_part(db: Session, target_part: str) -> List[models.Exercise]:
    return db.query(models.Exercise).filter(models.Exercise.target_part == target_part).all()

def get_exercise_by_id(db: Session, exercise_id: int) -> Optional[models.Exercise]:
    return db.query(models.Exercise).filter(models.Exercise.id == exercise_id).first()

def get_workout_logs_by_exercise_id(db: Session, exercise_id: int) -> List[models.WorkoutLog]:
    return db.query(models.WorkoutLog)\
             .filter(models.WorkoutLog.exercise_id == exercise_id)\
             .order_by(models.WorkoutLog.date.asc())\
             .all()

def create_workout_log(db: Session, log_data: schemas.WorkoutLogCreate) -> models.WorkoutLog:
    db_log = models.WorkoutLog(
        exercise_id=log_data.exercise_id,
        date=log_data.date,
        weight=log_data.weight,
        reps=log_data.reps,
        sets=log_data.sets
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def load_initial_exercises_from_csv(db: Session):
    if db.query(models.Exercise).first():
        print("운동 데이터가 이미 존재합니다. 초기 데이터 로드를 건너<0xEB><0x8A><0x95>니다.")
        return

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    csv_file_path = os.path.join(project_root, 'data', 'initial_exercises.csv')

    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                if not get_exercise_by_name(db, name=row['name']):
                    exercise_data = schemas.ExerciseCreate(name=row['name'], target_part=row['target_part'])
                    create_exercise(db, exercise_data) # 이미 commit 포함
            print("초기 운동 데이터가 로드되었습니다.")
    except FileNotFoundError:
        print(f"경고: 초기 데이터 파일({csv_file_path})을 찾을 수 없습니다.")
    except Exception as e:
        # create_exercise에서 이미 롤백 처리가 될 수 있지만, 전체 로직에 대한 롤백
        db.rollback()
        print(f"초기 데이터 로드 중 오류 발생: {e}")


