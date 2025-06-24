# app/pipelines/dream_pipeline.py
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict, Any, Tuple
import json

# 서비스 임포트
from ..services.audio_service import AudioService
from ..services.analysis_service import AnalysisService
from ..services.image_service import ImageService
from ..core.settings import settings # 설정 임포트
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DreamPipeline:
    def __init__(self,
                 audio_service: AudioService,
                 analysis_service: AnalysisService,
                 image_service: ImageService):
        self.audio_service = audio_service
        self.analysis_service = analysis_service
        self.image_service = image_service
        # LLM은 analysis_service에서 주로 사용되므로 여기서는 직접 초기화하지 않아도 됩니다.
        # 필요하다면 여기서 초기화하여 파이프라인 전용으로 사용 가능
        # self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7, openai_api_key=settings.OPENAI_API_KEY)

    async def run_analysis_and_image_stages(self, dream_text: str) -> Tuple[Dict[str, Any], str, str]:
        """
        STAGE 2: 꿈 텍스트 분석 (RAG, GPT-4o)
        STAGE 3: 분석 결과를 바탕으로 원본 이미지 생성 (DALL-E 3)
        STAGE 4: 치유 이미지 생성 (DALL-E 3)
        """
        logger.info(f"Starting STAGE 2: Analyzing dream text...")
        analysis_results = await self.analysis_service.analyze_dream(dream_text)
        logger.debug(f"Analysis Results: {analysis_results}")

        # 분석 결과에서 이미지 생성 프롬프트 추출 또는 생성
        original_image_prompt = analysis_results.get("image_prompt_original", f"A vivid surreal image representing the dream: {dream_text[:100]}...")
        healing_image_prompt = analysis_results.get("image_prompt_healing", f"A peaceful, positive and healing image related to the dream: {dream_text[:100]}...")

        logger.info(f"Starting STAGE 3: Generating original image...")
        original_image_url = await self.image_service.generate_image(original_image_prompt)
        logger.info(f"Original image URL: {original_image_url}")

        logger.info(f"Starting STAGE 4: Generating healing image...")
        healing_image_url = await self.image_service.generate_healing_image(healing_image_prompt)
        logger.info(f"Healing image URL: {healing_image_url}")

        return analysis_results, original_image_url, healing_image_url

    async def run_irt_stage(self, dream_text: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        STAGE 5: IRT (Imagery Rescripting Therapy) 분석 수행
        """
        logger.info(f"Starting STAGE 5: Performing IRT analysis...")
        irt_results = await self.analysis_service.perform_irt(dream_text, analysis_results)
        logger.debug(f"IRT Results: {irt_results}")
        return irt_results

    # STAGE 1은 API 라우터에서 직접 audio_service 호출
    # 전체 파이프라인 (필요 시 단일 엔드포인트에서 모든 스테이지 실행)
    # async def run_full_pipeline(self, audio_file_content: bytes) -> Dict[str, Any]:
    #     logger.info("Running full pipeline...")
    #     dream_text = await self.audio_service.speech_to_text(audio_file_content)
    #     analysis_results, original_image_url, healing_image_url = await self.run_analysis_and_image_stages(dream_text)
    #     irt_results = await self.run_irt_stage(dream_text, analysis_results)

    #     return {
    #         "dream_text": dream_text,
    #         "analysis_results": analysis_results,
    #         "original_image_url": original_image_url,
    #         "healing_image_url": healing_image_url,
    #         "irt_results": irt_results
    #     }