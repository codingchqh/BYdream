# 📂 파일 경로: app/schemas/dream_schema.py
# ⚠️ 이 파일에는 오직 Pydantic 모델 정의만 있어야 합니다.
# ⚠️ 'app' 변수나 라우터 관련 코드가 있다면 모두 삭제해주세요.

from pydantic import BaseModel, Field

# --- 요청(Request) 데이터 모델 ---

class DreamAnalysisRequest(BaseModel):
    """꿈 분석을 요청할 때 사용하는 데이터 모델"""
    dream_text: str = Field(
        ...,
        title="사용자의 꿈 내용",
        description="분석을 원하는 사용자의 꿈 텍스트입니다.",
        min_length=10,
        examples=["어젯밤에 하늘을 나는 꿈을 꿨어요. 기분이 정말 좋았어요."]
    )
    user_id: str | None = Field(
        default=None,
        title="사용자 ID",
        description="요청한 사용자를 식별하기 위한 ID입니다.",
        examples=["user-1234"]
    )


# --- 응답(Response) 데이터 모델 ---

class DreamAnalysisResponse(BaseModel):
    """꿈 분석 결과를 응답할 때 사용하는 데이터 모델"""
    session_id: str
    status: str = "received"
    message: str