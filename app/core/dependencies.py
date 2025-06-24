# app/core/dependencies.py
from fastapi import Depends
# 서비스 클래스들을 임포트합니다.
from ..services.audio_service import AudioService
from ..services.analysis_service import AnalysisService
from ..services.image_service import ImageService
# 파이프라인 클래스를 임포트합니다.
from ..piplines.dream_pipeline import DreamPipeline
from ..utils.logger import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------
# 서비스 인스턴스를 제공하는 의존성 함수들
# 각 요청마다 새로운 인스턴스를 생성하거나, 싱글턴 패턴을 적용할 수 있습니다.
# 여기서는 단순화를 위해 매 요청마다 새 인스턴스를 생성하는 것으로 가정합니다.
# ----------------------------------------------------
def get_audio_service() -> AudioService:
    """오디오 서비스 인스턴스를 반환합니다."""
    # 실제 애플리케이션에서는 서비스 초기화 시 필요한 의존성을 주입할 수 있습니다.
    logger.debug("Providing AudioService instance.")
    return AudioService()

def get_analysis_service() -> AnalysisService:
    """분석 서비스 인스턴스를 반환합니다."""
    logger.debug("Providing AnalysisService instance.")
    return AnalysisService()

def get_image_service() -> ImageService:
    """이미지 서비스 인스턴스를 반환합니다."""
    logger.debug("Providing ImageService instance.")
    return ImageService()

# ----------------------------------------------------
# DreamPipeline 인스턴스를 제공하는 의존성 함수
# 이 함수는 위에 정의된 서비스 의존성을 주입받아 파이프라인을 구성합니다.
# ----------------------------------------------------
def get_dream_pipeline(
    audio_service: AudioService = Depends(get_audio_service),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    image_service: ImageService = Depends(get_image_service)
) -> DreamPipeline:
    """
    DreamPipeline 인스턴스를 반환합니다.
    내부적으로 AudioService, AnalysisService, ImageService를 주입받습니다.
    """
    logger.debug("Providing DreamPipeline instance.")
    return DreamPipeline(audio_service, analysis_service, image_service)

# 이 외에 사용자 인증, 권한 부여 등 다양한 의존성을 여기에 정의할 수 있습니다.