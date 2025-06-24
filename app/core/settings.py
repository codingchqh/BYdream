# app/core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # .env 파일에서 환경 변수를 로드하도록 설정합니다.
    # .env 파일이 없으면 시스템 환경 변수에서 찾습니다.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

# 설정이 제대로 로드되었는지 확인하는 간단한 로깅 (선택 사항)
# print(f"--- Settings Loaded ---")
# print(f"Project Name: {settings.PROJECT_NAME}")
# print(f"OpenAI API Key (first 5 chars): {settings.OPENAI_API_KEY[:5]}...")
# print(f"Chroma DB Path: {settings.CHROMA_DB_PATH}")
# print(f"Database URL: {settings.DATABASE_URL}")
# print(f"Log Level: {settings.LOG_LEVEL}")
# print(f"-----------------------")