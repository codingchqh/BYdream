# app/database/session.py
from sqlalchemy.ext.asyncio import AsyncSession
from .connection import AsyncSessionLocal
from ..utils.logger import get_logger
from typing import AsyncGenerator, Any # AsyncGenerator를 임포트합니다.

logger = get_logger(__name__)

# 함수의 반환 타입 힌트를 AsyncSession이 아닌 AsyncGenerator로 변경합니다.
# AsyncGenerator[YieldType, SendType, ReturnType]
# 여기서는 yield AsyncSession이므로 YieldType은 AsyncSession
# SendType은 사용하지 않으므로 Any
# ReturnType은 사용하지 않으므로 Any
async def get_db() -> AsyncGenerator[AsyncSession, Any]: # 이 부분을 수정합니다.
    """
    FastAPI 의존성 주입을 위한 데이터베이스 세션 제공자.
    요청마다 새로운 세션을 생성하고, 응답 후 세션을 닫습니다.
    """
    db = AsyncSessionLocal()
    try:
        yield db # 여기서 AsyncSession 객체를 yield 합니다.
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        # 예외 발생 시 세션 롤백 (선택 사항, 필요에 따라 추가)
        # await db.rollback()
        raise # 예외를 다시 발생시켜 FastAPI가 처리하도록 함
    finally:
        await db.close() # 요청 완료 후 세션 닫기