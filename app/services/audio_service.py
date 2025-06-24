# app/services/audio_service.py
import openai # OpenAI Python SDK
import io # 바이트 스트림 처리를 위해 필요
from ..core.settings import settings # 설정 정보 로드
from ..utils.logger import get_logger # 로깅을 위해 임포트
from ..utils.exceptions import AIModelException, ServiceException # 커스텀 예외

logger = get_logger(__name__)

class AudioService:
    def __init__(self):
        # OpenAI API 키 설정 (settings.py에서 로드)
        openai.api_key = settings.OPENAI_API_KEY
        self.openai_client = openai.AsyncClient() # 비동기 OpenAI 클라이언트 초기화

    async def speech_to_text(self, audio_content: bytes) -> str:
        """
        Whisper API를 사용하여 음성 파일을 텍스트로 변환합니다.
        """
        try:
            # BytesIO를 사용하여 바이트 컨텐츠를 파일처럼 처리
            audio_file = io.BytesIO(audio_content)
            audio_file.name = "dream_audio.wav" # 파일 이름은 API 요청에 필요 (확장자도 중요)

            logger.info("Calling OpenAI Whisper API for STT...")
            response = await self.openai_client.audio.transcriptions.create(
                model=settings.WHISPER_MODEL_NAME, # settings에서 모델명 로드 (예: "whisper-1")
                file=audio_file
            )
            logger.info("STT successful.")
            return response.text
        except openai.APIStatusError as e: # OpenAI API 호출 시 발생하는 HTTP 상태 코드 에러
            logger.error(f"OpenAI API status error during STT: {e.status_code} - {e.response}", exc_info=True)
            raise AIModelException(f"OpenAI API error during STT: {e.message} (Status: {e.status_code})")
        except openai.APITimeoutError as e: # OpenAI API 호출 시 타임아웃 에러
            logger.error(f"OpenAI API timeout during STT: {e}", exc_info=True)
            raise AIModelException(f"OpenAI API timeout during STT.")
        except Exception as e: # 기타 예상치 못한 에러
            logger.error(f"Unexpected error during speech-to-text conversion: {e}", exc_info=True)
            raise ServiceException(f"Failed to convert audio to text: {e}")