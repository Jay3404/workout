from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import inspect as sqlalchemy_inspect # inspect 임포트 (이름 충돌 방지 위해 sqlalchemy_inspect로)
from typing import List, Optional # Python 3.9+ 에서는 List, Optional 불필요
import os

from . import crud, models, schemas
from .database import SessionLocal, engine, get_db

# DB 테이블 생성 (없을 경우)
# 애플리케이션 시작 시 한 번만 실행되도록 하는 것이 좋음
# 여기서는 간단하게 모듈 로드 시점에 호출
models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="오늘의 운동 추천 API", version="0.1.0")

# 정적 파일 마운트 (CSS, JS 등)
# __file__은 현재 파일(main.py)의 경로
# os.path.dirname(__file__)은 app 디렉토리
# os.path.join(os.path.dirname(__file__), "static")은 app/static 디렉토리
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 템플릿 설정
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

@app.on_event("startup")
async def startup_event():
    # --- 데이터베이스 연결 및 스키마 검증 ---
    print("--- 애플리케이션 시작: 데이터베이스 연결 및 스키마 검증 ---")
    try:
        inspector = sqlalchemy_inspect(engine)  # 여기서 engine을 사용합니다.
        table_names = inspector.get_table_names()

        print(f"데이터베이스 연결 성공. 발견된 테이블 목록: {table_names}")

        expected_tables = ["exercises", "workout_logs"]
        all_expected_tables_found = True
        for table_name in expected_tables:
            if table_name in table_names:
                print(f"테이블 '{table_name}'이(가) 데이터베이스에 존재합니다.")
                # 컬럼 정보도 확인할 수 있습니다 (필요한 경우 주석 해제)
                # columns = inspector.get_columns(table_name)
                # print(f"'{table_name}' 테이블의 컬럼: {[col['name'] for col in columns]}")
            else:
                print(f"경고: 예상된 테이블 '{table_name}'을(를) 데이터베이스에서 찾을 수 없습니다!")
                all_expected_tables_found = False

        if not table_names:
            print("경고: 데이터베이스에서 어떠한 테이블도 찾을 수 없습니다. 스키마가 생성되지 않았을 수 있습니다.")
        elif all_expected_tables_found:
            print("모든 예상 테이블이 데이터베이스에 존재합니다.")

    except Exception as e:
        print(f"오류: 데이터베이스 스키마 검증 중 예외 발생: {e}")
        print("데이터베이스 연결 설정(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)을 확인하세요.")
    print("--- 데이터베이스 스키마 검증 완료 ---")

    # --- CSV로부터 초기 데이터 로드 시도 ---
    # 이 부분은 DB 연결이 정상이라는 가정 하에 실행됩니다.
    # 만약 위에서 연결 오류가 있었다면, 여기서도 문제가 발생할 수 있습니다.
    db_session_for_csv_load = SessionLocal()
    try:
        print("--- exercises 테이블이 비어있을 경우 CSV에서 초기 데이터 로드 시도 ---")
        crud.load_initial_exercises_from_csv(db_session_for_csv_load)
    except Exception as e:
        print(f"CSV 데이터 로드 중 오류 발생: {e}")
    finally:
        db_session_for_csv_load.close()
    print("--- 애플리케이션 시작 준비 완료 ---")

@app.get("/", response_class=HTMLResponse, summary="메인 페이지")
async def read_root(request: Request, db: Session = Depends(get_db)):
    """
    메인 HTML 페이지를 렌더링하고 운동 부위 목록을 전달합니다.
    """
    body_parts = crud.get_distinct_target_parts(db) # 여기서 body_parts를 가져옵니다.
    # 디버깅을 위해 body_parts 내용을 출력해볼 수 있습니다.
    print(f"Fetched body_parts: {body_parts}")
    return templates.TemplateResponse("index.html", {"request": request, "body_parts": body_parts})
@app.post("/get_exercises", response_model=schemas.ExerciseListResponse, summary="부위별 운동 추천")
async def get_exercises_for_body_part(
    body_part_req: schemas.BodyPartRequest,
    db: Session = Depends(get_db)
):
    """
    선택된 신체 부위에 해당하는 운동 목록을 반환합니다.
    - **body_part**: 운동을 원하는 신체 부위 (예: "등", "가슴")
    """
    exercises_db = crud.get_exercises_by_target_part(db, target_part=body_part_req.body_part)
    if not exercises_db:
        # HTTPException 대신 JSONResponse로 커스텀 오류 메시지 가능
        # raise HTTPException(status_code=404, detail="해당 부위의 운동이 없습니다.")
        return JSONResponse(status_code=404, content={"exercises": [], "message": "해당 부위의 운동이 없습니다."})
    return {"exercises": exercises_db}


@app.post("/get_exercise_history", response_model=schemas.ExerciseHistoryResponse, summary="운동 기록 조회")
async def get_exercise_history(
    history_req: schemas.ExerciseHistoryRequest,
    db: Session = Depends(get_db)
):
    """
    특정 운동의 무게 변화 추이 및 기록을 반환합니다.
    - **exercise_id**: 기록을 조회할 운동의 ID
    """
    exercise = crud.get_exercise_by_id(db, exercise_id=history_req.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="운동을 찾을 수 없습니다.")

    logs = crud.get_workout_logs_by_exercise_id(db, exercise_id=history_req.exercise_id)
    return {"exercise_name": exercise.name, "history": logs}

@app.post("/add_log", response_model=schemas.MessageResponse, status_code=201, summary="운동 기록 추가")
async def add_new_workout_log(
    log_data: schemas.WorkoutLogCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 운동 기록을 데이터베이스에 추가합니다.
    - **exercise_id**: 기록할 운동의 ID
    - **date**: 운동 날짜 (YYYY-MM-DD)
    - **weight**: 무게 (kg)
    - **reps**: 반복 횟수
    - **sets**: 세트 수
    """
    exercise = crud.get_exercise_by_id(db, exercise_id=log_data.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="기록을 추가하려는 운동을 찾을 수 없습니다.")

    try:
        crud.create_workout_log(db, log_data=log_data)
        return {"message": f"{exercise.name} 운동 기록이 성공적으로 추가되었습니다."}
    except Exception as e:
        # 실제 운영 환경에서는 더 구체적인 오류 로깅 및 처리가 필요
        raise HTTPException(status_code=500, detail=f"기록 저장 중 오류 발생: {str(e)}")

# FastAPI 자동 문서 (Swagger UI: /docs, ReDoc: /redoc)