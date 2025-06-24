# 📂 파일 경로: app/main.py

from fastapi import FastAPI
# api 폴더의 dream_routes 파일을 가져옵니다.
from app.api import dream_routes

# FastAPI 앱의 본체인 'app'을 정의합니다.
app = FastAPI(
    title="보여dream API",
    version="0.1.0",
)

# dream_routes 파일에서 정의한 'router'를 'app'에 포함시킵니다.
app.include_router(dream_routes.router)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "안녕하세요, '보여dream' API 서버입니다."}