# app/core/settings.py
from pydantic_settings import BaseSettings # SettingsConfigDict 임포트 제거
# import os # os 모듈이 다른 곳에서 사용되지 않는다면 제거해도 무방합니다.

class Settings(BaseSettings):
    # .env 파일에서 환경 변수를 로드하는 설정을 완전히 제거합니다.
    # 이제 Pydantic은 오직 시스템 환경 변수에서만 값을 찾습니다.
    # model_config = SettingsConfigDict(env_file=".env", extra="ignore") # 이 줄을 제거합니다.

    PROJECT_NAME: str = "My Dream Project"
    PROJECT_VERSION: str = "0.1.0"

    # API Keys (필수 환경 변수)
    OPENAI_API_KEY: str
    DEEPL_API_KEY: str = None # 선택 사항

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./sql_app.db" # 비동기 SQLite DB

    # RAG Settings
    CHROMA_DB_PATH: str = "./data/vector_store"
    RAG_CHUNK_SIZE: int = 1000
    
    RAG_CHUNK_OVERLAP: int = 200

    # AI Model Settings
    DALL_E_IMAGE_SIZE: str = "1024x1024"
    DALL_E_IMAGE_QUALITY: str = "standard"
    WHISPER_MODEL_NAME: str = "whisper-1"

    # Environment
    ENVIRONMENT: str = "development"

    # Logging Level
    LOG_LEVEL: str = "INFO" # INFO, DEBUG, WARNING, ERROR, CRITICAL


settings = Settings()