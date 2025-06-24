# app/utils/logger.py
import logging
from ..core.settings import settings # settings.py에서 LOG_LEVEL을 가져오기 위해 임포트

def get_logger(name: str) -> logging.Logger:
    """
    프로젝트 전반에 걸쳐 사용될 로거 인스턴스를 반환합니다.
    settings.py에 정의된 LOG_LEVEL을 따릅니다.
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper()) # settings에서 로깅 레벨 가져오기

    # 핸들러 중복 추가 방지
    if not logger.handlers:
        # 콘솔 핸들러 (StreamHandler) 설정
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# 예시:
# from app.utils.logger import get_logger
# logger = get_logger(__name__)
# logger.info("This is an info message.")