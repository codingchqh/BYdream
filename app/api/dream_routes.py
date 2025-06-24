# app/api/dream_routes.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession # 비동기 DB 세션 타입
from sqlalchemy import select # DB 쿼리를 위해 필요
from typing import List, Dict, Any

# 내부 모듈 임포트
from ..schemas.dream_schema import DreamAnalysisResponse, DreamSessionResponse, IrtAnalysisResponse
from ..piplines.dream_pipeline import DreamPipeline # 파이프라인
from ..database.session import get_db # DB 세션 의존성 주입 함수
from ..core.dependencies import get_dream_pipeline # 파이프라인 의존성 주입 함수
from ..models.dream_model import DreamSession as DBDreamSession # DB 모델 임포트
from ..utils.logger import get_logger # 로깅
from ..utils.exceptions import NotFoundException, BadRequestException, ServiceException # 커스텀 예외

router = APIRouter()
logger = get_logger(__name__)

# 예외 핸들러는 main.py 또는 별도의 파일에서 전역적으로 설정할 수 있습니다.
# 여기서는 ServiceException 발생 시 HTTPException으로 변환하여 반환합니다.
@router.post("/sessions", response_model=DreamSessionResponse, status_code=status.HTTP_201_CREATED, summary="새로운 꿈 분석 세션을 시작하고 음성을 텍스트로 변환")
async def create_dream_session(
    audio_file: UploadFile = File(..., description="사용자의 꿈 내용이 담긴 음성 파일 (WAV, MP3 등)"),
    db: AsyncSession = Depends(get_db), # DB 세션 주입
    pipeline: DreamPipeline = Depends(get_dream_pipeline) # 파이프라인 주입
):
    """
    사용자의 꿈 내용을 담은 음성 파일을 업로드하여 새로운 분석 세션을 시작합니다.
    업로드된 음성은 STAGE 1 (음성-텍스트 변환)을 통해 텍스트로 변환되어 세션에 저장됩니다.
    """
    logger.info(f"API Call: create_dream_session - received file '{audio_file.filename}' ({audio_file.content_type})")
    try:
        audio_content = await audio_file.read()

        # STAGE 1: 음성-텍스트 변환
        dream_text = await pipeline.audio_service.speech_to_text(audio_content)
        logger.info(f"STT successful for new session. Text: '{dream_text[:50]}...'")

        # 새 DreamSession DB 모델 인스턴스 생성 및 저장
        db_session = DBDreamSession(dream_text=dream_text)
        db.add(db_session) # DB에 추가
        await db.commit() # 변경사항 커밋
        await db.refresh(db_session) # DB에서 최신 상태로 새로고침 (id, created_at 등 포함)

        logger.info(f"Dream session {db_session.id} created successfully.")
        return DreamSessionResponse.model_validate(db_session) # Pydantic 모델로 변환하여 응답 (v2)
    except ServiceException as e:
        logger.error(f"Service error in create_dream_session: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.critical(f"Unhandled error in create_dream_session: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.get("/sessions/{session_id}", response_model=DreamSessionResponse, summary="특정 꿈 분석 세션 정보 조회")
async def get_dream_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """
    특정 `session_id`에 해당하는 꿈 분석 세션의 상세 정보를 조회합니다.
    """
    logger.info(f"API Call: get_dream_session - session_id: {session_id}")
    try:
        # DB에서 세션 조회
        result = await db.execute(select(DBDreamSession).filter(DBDreamSession.id == session_id))
        session = result.scalars().first() # 첫 번째 결과 가져오기

        if not session:
            logger.warning(f"Session with ID {session_id} not found.")
            raise NotFoundException(f"Session with ID {session_id} not found.")
        
        return DreamSessionResponse.model_validate(session) # Pydantic 모델로 변환
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.critical(f"Unhandled error in get_dream_session: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")


@router.post("/sessions/{session_id}/analyze", response_model=DreamAnalysisResponse, summary="세션의 꿈 텍스트를 분석하고 이미지 생성")
async def analyze_dream_and_generate_image(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    pipeline: DreamPipeline = Depends(get_dream_pipeline)
):
    """
    기존 세션의 꿈 텍스트를 바탕으로 심층 분석을 수행하고,
    분석 결과에 기반한 DALL-E 이미지를 생성합니다 (STAGE 2, 3, 4).
    """
    logger.info(f"API Call: analyze_dream_and_generate_image - session_id: {session_id}")
    try:
        # DB에서 세션 조회
        result = await db.execute(select(DBDreamSession).filter(DBDreamSession.id == session_id))
        session = result.scalars().first()

        if not session:
            logger.warning(f"Session with ID {session_id} not found for analysis.")
            raise NotFoundException(f"Session with ID {session_id} not found.")
        
        if not session.dream_text:
            logger.warning(f"Dream text missing for session {session_id} before analysis.")
            raise BadRequestException(f"Dream text missing for session {session_id}. Please create session with audio first.")

        # 파이프라인의 STAGE 2-4 실행 (분석 및 이미지 생성)
        analysis_result_dict, generated_image_url, healing_image_url = await pipeline.run_analysis_and_image_stages(session.dream_text)

        # DB 세션 업데이트
        session.analysis_results = analysis_result_dict # 분석 결과 저장
        # 이미지 URL은 리스트 형태로 저장될 수 있도록 합니다.
        if session.generated_images is None:
            session.generated_images = []
        session.generated_images.append({"original": str(generated_image_url), "healing": str(healing_image_url)})
        
        await db.commit() # 변경사항 커밋
        await db.refresh(session) # DB에서 최신 상태로 새로고침

        logger.info(f"Dream analysis and image generation completed for session {session_id}.")
        return DreamAnalysisResponse(
            session_id=session_id,
            analysis_results=analysis_result_dict,
            generated_image_url=generated_image_url,
            healing_image_url=healing_image_url
        )
    except (NotFoundException, BadRequestException, ServiceException) as e:
        logger.error(f"Service error in analyze_dream_and_generate_image: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.critical(f"Unhandled error in analyze_dream_and_generate_image: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")

@router.post("/sessions/{session_id}/irt", response_model=IrtAnalysisResponse, summary="IRT(Imagery Rescripting Therapy) 분석 수행")
async def perform_irt_analysis(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    pipeline: DreamPipeline = Depends(get_dream_pipeline)
):
    """
    특정 `session_id`의 꿈 텍스트에 대해 IRT(Imagery Rescripting Therapy) 분석을 수행합니다 (STAGE 5).
    """
    logger.info(f"API Call: perform_irt_analysis - session_id: {session_id}")
    try:
        # DB에서 세션 조회
        result = await db.execute(select(DBDreamSession).filter(DBDreamSession.id == session_id))
        session = result.scalars().first()

        if not session:
            logger.warning(f"Session with ID {session_id} not found for IRT analysis.")
            raise NotFoundException(f"Session with ID {session_id} not found.")
        
        if not session.analysis_results:
            logger.warning(f"Analysis results missing for session {session_id} before IRT.")
            raise BadRequestException(f"Analysis must be performed for session {session_id} before IRT.")

        # 파이프라인의 STAGE 5 실행 (IRT 분석)
        irt_results_dict = await pipeline.run_irt_stage(session.dream_text, session.analysis_results)

        # DB 세션 업데이트
        session.irt_results = irt_results_dict # IRT 결과 저장
        await db.commit() # 변경사항 커밋
        await db.refresh(session) # DB에서 최신 상태로 새로고침

        logger.info(f"IRT analysis completed for session {session_id}.")
        return IrtAnalysisResponse(
            session_id=session_id,
            irt_results=irt_results_dict
        )
    except (NotFoundException, BadRequestException, ServiceException) as e:
        logger.error(f"Service error in perform_irt_analysis: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.critical(f"Unhandled error in perform_irt_analysis: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")