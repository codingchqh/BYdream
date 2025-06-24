# app/services/audio_service.py
import openai
import io
from ..core.settings import settings
from ..utils.logger import get_logger
from ..utils.exceptions import ServiceException

logger = get_logger(__name__)

class AudioService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.openai_client = openai.AsyncClient()

    async def speech_to_text(self, audio_content: bytes) -> str:
        """
        Whisper API를 사용하여 음성 파일을 텍스트로 변환합니다.
        """
        try:
            audio_file = io.BytesIO(audio_content)
            audio_file.name = "dream_audio.wav" # 파일 이름은 API 요청에 필요

            logger.info("Calling OpenAI Whisper API for STT...")
            response = await self.openai_client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL_NAME, # settings에서 모델명 로드
                file=audio_file
            )
            return response.text
        except openai.APIError as e:
            logger.error(f"OpenAI API error during STT: {e}", exc_info=True)
            raise ServiceException(f"OpenAI API error during STT: {e}")
        except Exception as e:
            logger.error(f"Error during speech-to-text conversion: {e}", exc_info=True)
            raise ServiceException(f"Failed to convert audio to text: {e}")