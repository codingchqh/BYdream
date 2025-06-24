# app/schemas/dream_schema.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime # datetime 객체를 위한 임포트

# Pydantic 모델은 FastAPI의 요청/응답 유효성 검사 및 문서화에 사용됩니다.

class DreamSessionCreate(BaseModel):
    """
    새로운 꿈 세션을 생성하기 위한 요청 모델 (현재는 음성 파일로 생성하므로 직접 사용되지는 않음).
    만약 텍스트로 세션을 생성하는 API가 있다면 사용될 수 있습니다.
    """
    dream_text: str = Field(..., description="사용자의 꿈 내용 텍스트")

class DreamAnalysisResult(BaseModel):
    """
    꿈 분석 결과의 상세 내용을 정의하는 모델.
    """
    summary: str = Field(..., description="꿈의 핵심 내용 요약")
    keywords: List[str] = Field(..., description="꿈의 주요 키워드 목록")
    symbolism_analysis: str = Field(..., description="꿈의 주요 상징에 대한 심리학적 해석")
    emotional_context: str = Field(..., description="꿈 속 감정 상태 및 의미 분석")
    potential_implications: str = Field(..., description="꿈이 현재 삶에 시사하는 바 또는 메시지")
    image_prompt_original: str = Field(..., description="원본 꿈 이미지를 생성하기 위한 DALL-E 프롬프트 (영어)")
    image_prompt_healing: str = Field(..., description="치유 이미지를 생성하기 위한 DALL-E 프롬프트 (영어)")

class IrtRescriptingSuggestion(BaseModel):
    """
    IRT(Imagery Rescripting Therapy)의 재구성 제안 항목 모델.
    """
    element: str = Field(..., description="재구성할 꿈의 부정적 요소")
    original_image: str = Field(..., description="원본 꿈 속 부정적 이미지에 대한 설명")
    new_image_suggestion: str = Field(..., description="새로운 긍정적 이미지에 대한 구체적인 상상 지침")

class IrtAnalysisResult(BaseModel):
    """
    IRT 분석 결과의 상세 내용을 정의하는 모델.
    """
    irt_explanation: str = Field(..., description="IRT(심상 재구성 치료)에 대한 간략한 설명")
    negative_elements_identified: List[str] = Field(..., description="원본 꿈에서 재구성할 필요가 있는 부정적 요소 식별 목록")
    rescripting_suggestions: List[IrtRescriptingSuggestion] = Field(..., description="부정적 이미지를 긍정적으로 재구성하기 위한 구체적인 제안 목록")
    actionable_insights: str = Field(..., description="IRT 과정을 통해 얻을 수 있는 통찰 및 실제 생활에 적용 가능한 조언")

class DreamAnalysisResponse(BaseModel):
    """
    꿈 분석 및 이미지 생성 API 응답 모델.
    """
    session_id: int = Field(..., description="해당 분석이 속한 세션의 고유 ID")
    analysis_results: DreamAnalysisResult = Field(..., description="꿈 심층 분석 결과")
    generated_image_url: HttpUrl = Field(..., description="원본 꿈 분위기를 기반으로 생성된 이미지의 URL")
    healing_image_url: HttpUrl = Field(..., description="치유적인 분위기를 기반으로 생성된 이미지의 URL")

class IrtAnalysisResponse(BaseModel):
    """
    IRT 분석 API 응답 모델.
    """
    session_id: int = Field(..., description="해당 IRT 분석이 속한 세션의 고유 ID")
    irt_results: IrtAnalysisResult = Field(..., description="IRT 분석 결과")

class DreamSessionResponse(BaseModel):
    """
    꿈 분석 세션 정보를 나타내는 응답 모델 (데이터베이스 모델과 직접 매핑).
    """
    id: int = Field(..., description="꿈 분석 세션의 고유 ID")
    dream_text: str = Field(..., description="사용자가 말한 꿈 텍스트")
    analysis_results: Optional[DreamAnalysisResult] = Field(None, description="꿈 심층 분석 결과 (분석 전에는 None)")
    irt_results: Optional[IrtAnalysisResult] = Field(None, description="IRT 분석 결과 (IRT 수행 전에는 None)")
    generated_images: List[Dict[str, HttpUrl]] = Field([], description="생성된 이미지 URL 목록 (예: [{'original': 'url', 'healing': 'url'}])")
    created_at: datetime = Field(..., description="세션 생성 시간")
    updated_at: datetime = Field(..., description="세션 마지막 업데이트 시간")

    # ORM 모드 설정 (SQLAlchemy 모델과 Pydantic 모델 간의 변환을 용이하게 함)
    # Pydantic v2에서는 `orm_mode = True` 대신 `from_attributes = True`를 사용합니다.
    model_config = {
        "from_attributes": True # Pydantic v2 방식
    }