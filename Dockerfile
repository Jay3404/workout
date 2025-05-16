# Python 런타임 환경을 베이스 이미지로 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY ./app /app/app
#COPY ./data /app/data

# 포트 노출 (Uvicorn 기본 포트 8000)
EXPOSE 8000

# 애플리케이션 실행 (Uvicorn 사용)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# --reload 옵션은 개발 시 유용, 프로덕션에서는 제거하거나 gunicorn + uvicorn worker 사용 고려
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]