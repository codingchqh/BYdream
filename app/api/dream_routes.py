#📂 파일 경로: app/api/dream_routes.py

import uuid
from fastapi import APIRouter, status
# schemas 폴더의 dream_schema 파일에서 정의한 모델들을 가져옵니다.
from app.schemas import dream_schema

# 'router'라는 이름의 변수를 정확하게 정의합니다.
router = APIRouter(
    prefix="/api/v1",
    tags=["Dream Analysis"],
)


@router.post(
    "/analyze-dream",
    response_model=dream_schema.DreamAnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def analyze_dream(request: dream_schema.DreamAnalysisRequest):
    session_id = f"sess_{uuid.uuid4().hex}"
    
    return dream_schema.DreamAnalysisResponse(
        session_id=session_id,
        message="성공적으로 꿈 분석 요청이 접수되었습니다."
    )