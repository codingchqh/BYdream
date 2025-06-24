# app/main.py

from fastapi import FastAPI
from app.api import dream_routes # 위에서 만든 dream_routes를 가져옵니다.

# FastAPI 애플리케이션 인스턴스를 생성합니다.
app = FastAPI(
    title="보여dream API",
    description="AI 기반 꿈 분석 및 심리 치유 서비스 '보여dream'의 API 서버입니다.",
    version="0.1.0",
    contact={
        "name": "Team BYDream",
        "url": "https://bydream.io/contact", # 예시 URL
    },
)

# dream_routes.py 파일에서 정의한 라우터를 앱에 포함시킵니다.
app.include_router(dream_routes.router)


# 서버의 루트 경로('/')로 접속했을 때 간단한 환영 메시지를 반환합니다.
@app.get("/", tags=["Root"])
async def read_root():
    """
    API 서버의 상태를 확인하는 루트 엔드포인트입니다.
    """
    return {"message": "안녕하세요, '보여dream' API 서버입니다."}

