# app/core/config.py
from pydantic_settings import BaseSettings # SettingsConfigDict 임포트 제거

class Settings(BaseSettings):
    # .env 파일에서 환경 변수를 로드하는 설정 (model_config)을 제거합니다.
    # 이제 Pydantic은 기본적으로 시스템 환경 변수에서 값을 찾습니다.

    PROJECT_NAME: str = "My Dream Project"
    PROJECT_VERSION: str = "0.1.0"

    OPENAI_API_KEY: str
    DEEPL_API_KEY: str = None # 필요하다면 추가 (번역 서비스 등)
    CHROMA_DB_PATH: str = "./data/chroma_db" # ChromaDB 저장 경로

    # RAG 관련 설정
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200

    # DALL-E 이미지 설정
    DALL_E_IMAGE_SIZE: str = "1024x1024" # "256x256", "512x512", "1024x1024"
    DALL_E_IMAGE_QUALITY: str = "standard" # "standard", "hd"

    # Whisper 모델 설정 (로컬 모델 사용 시)
    WHISPER_MODEL_SIZE: str = "base" # "tiny", "base", "small", "medium", "large"

    # 예시: 개발/운영 환경 구분
    ENVIRONMENT: str = "development" # "development", "production", "testing"


settings = Settings()

# 설정이 제대로 로드되었는지 확인하는 간단한 로깅 (선택 사항)
# print(f"--- Settings Loaded ---")
# print(f"Project Name: {settings.PROJECT_NAME}")
# print(f"OpenAI API Key (first 5 chars): {settings.OPENAI_API_KEY[:5]}...")
# print(f"Chroma DB Path: {settings.CHROMA_DB_PATH}")
# print(f"-----------------------")