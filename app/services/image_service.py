# app/services/image_service.py
import openai # OpenAI Python SDK
from ..core.settings import settings # 설정 정보 로드
from ..utils.logger import get_logger # 로깅을 위해 임포트
from ..utils.exceptions import AIModelException, ServiceException # 커스텀 예외

logger = get_logger(__name__)

class ImageService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.openai_client = openai.AsyncClient() # 비동기 OpenAI 클라이언트 초기화

    async def generate_image(self, prompt: str) -> str:
        """
        DALL-E 3를 사용하여 주어진 프롬프트로 이미지를 생성하고 URL을 반환합니다.
        """
        try:
            logger.info(f"Generating original image with prompt: '{prompt[:100]}...'")
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1, # 생성할 이미지 수
                size=settings.DALL_E_IMAGE_SIZE, # settings에서 이미지 크기 로드
                quality=settings.DALL_E_IMAGE_QUALITY # settings에서 이미지 품질 로드
            )
            image_url = response.data[0].url
            logger.info(f"Original image generated: {image_url}")
            return image_url
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API status error during image generation: {e.status_code} - {e.response}", exc_info=True)
            raise AIModelException(f"OpenAI API error during image generation: {e.message} (Status: {e.status_code})")
        except openai.APITimeoutError as e:
            logger.error(f"OpenAI API timeout during image generation: {e}", exc_info=True)
            raise AIModelException(f"OpenAI API timeout during image generation.")
        except Exception as e:
            logger.error(f"Unexpected error generating image: {e}", exc_info=True)
            raise ServiceException(f"Failed to generate image: {e}")

    async def generate_healing_image(self, prompt: str) -> str:
        """
        DALL-E 3를 사용하여 치유적인 분위기의 이미지를 생성합니다.
        """
        # 치유 이미지 프롬프트에 명확성을 더하기 위해 키워드를 추가합니다.
        healing_prompt = f"A peaceful, positive, hopeful, and healing interpretation of: {prompt}"
        logger.info(f"Generating healing image with prompt: '{healing_prompt[:100]}...'")
        return await self.generate_image(healing_prompt)