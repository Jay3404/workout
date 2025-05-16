import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv() # .env 파일에서 환경변수 로드

DB_USER = os.getenv('POSTGRES_USER', 'root')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'root')
DB_NAME = os.getenv('POSTGRES_DB', 'workoutdb')
DB_HOST = os.getenv('DB_HOST', 'db') # docker-compose 서비스 이름
DB_PORT = os.getenv('DB_PORT', '5432')

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB 세션 의존성 주입용 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()