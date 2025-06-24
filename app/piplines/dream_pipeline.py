# app/pipelines/dream_pipeline.py
from typing import Dict, Any, Tuple
# 서비스 클래스들을 임포트합니다.
from ..services.audio_service import AudioService
from ..services.analysis_service import AnalysisService
from ..services.image_service import ImageService
from ..utils.logger import get_logger # 로깅을 위해 임포트
from ..utils.exceptions import ServiceException

logger = get_logger(__name__)

class DreamPipeline:
    def __init__(self,
                 audio_service: AudioService,
                 analysis_service: AnalysisService,
                 image_service: ImageService):
        # 각 서비스 인스턴스를 주입받아 파이프라인 내부에서 사용합니다.
        self.audio_service = audio_service
        self.analysis_service = analysis_service
        self.image_service = image_service
        logger.info("DreamPipeline initialized with services.")

    async def run_analysis_and_image_stages(self, dream_text: str) -> Tuple[Dict[str, Any], str, str]:
        """
        꿈 분석 및 이미지 생성 스테이지 (STAGE 2, 3, 4)를 실행합니다.
        - STAGE 2: 꿈 텍스트 분석 (RAG, GPT-4o)
        - STAGE 3: 분석 결과를 바탕으로 원본 이미지 생성 (DALL-E 3)
        - STAGE 4: 치유 이미지 생성 (DALL-E 3)
        """
        logger.info(f"Starting STAGE 2: Analyzing dream text (first 50 chars): '{dream_text[:50]}...'")
        analysis_results = await self.analysis_service.analyze_dream(dream_text)
        logger.debug(f"Analysis Results received: {analysis_results}")

        # 분석 결과에서 이미지 생성 프롬프트 추출 또는 기본값 사용
        original_image_prompt = analysis_results.get("image_prompt_original", f"A vivid surreal image representing the dream: {dream_text[:100]}...")
        healing_image_prompt = analysis_results.get("image_prompt_healing", f"A peaceful, positive and healing image related to the dream: {dream_text[:100]}...")

        logger.info(f"Starting STAGE 3: Generating original image with prompt: '{original_image_prompt[:100]}...'")
        original_image_url = await self.image_service.generate_image(original_image_prompt)
        logger.info(f"Original image URL: {original_image_url}")

        logger.info(f"Starting STAGE 4: Generating healing image with prompt: '{healing_image_prompt[:100]}...'")
        healing_image_url = await self.image_service.generate_healing_image(healing_image_prompt)
        logger.info(f"Healing image URL: {healing_image_url}")

        return analysis_results, original_image_url, healing_image_url

    async def run_irt_stage(self, dream_text: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        IRT(Imagery Rescripting Therapy) 분석 스테이지 (STAGE 5)를 실행합니다.
        - STAGE 5: IRT 분석 수행
        """
        logger.info(f"Starting STAGE 5: Performing IRT analysis for text (first 50 chars): '{dream_text[:50]}...'")
        irt_results = await self.analysis_service.perform_irt(dream_text, analysis_results)
        logger.debug(f"IRT Results received: {irt_results}")
        return irt_results

    # STAGE 1 (음성-텍스트 변환)은 API 라우터에서 audio_service를 직접 호출하도록 설계되어 있습니다.
    # 필요한 경우, 모든 스테이지를 한 번에 실행하는 통합 파이프라인 메서드를 여기에 추가할 수 있습니다.
    # async def run_full_pipeline(self, audio_file_content: bytes) -> Dict[str, Any]:
    #     logger.info("Running full pipeline...")
    #     # STAGE 1
    #     dream_text = await self.audio_service.speech_to_text(audio_file_content)
    #     logger.info(f"Converted text (full pipeline): {dream_text[:100]}...")
    #     # STAGE 2-4
    #     analysis_results, original_image_url, healing_image_url = await self.run_analysis_and_image_stages(dream_text)
    #     # STAGE 5
    #     irt_results = await self.run_irt_stage(dream_text, analysis_results)

    #     return {
    #         "dream_text": dream_text,
    #         "analysis_results": analysis_results,
    #         "original_image_url": original_image_url,
    #         "healing_image_url": healing_image_url,
    #         "irt_results": irt_results
    #     }