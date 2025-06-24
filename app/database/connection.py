# app/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base # ORM Base 클래스
from ..core.settings import settings # settings.py에서 DB URL을 가져오기 위해 임포트
from ..utils.logger import get_logger # 로깅을 위해 임포트

logger = get_logger(__name__)

# 비동기 엔진 생성
# echo=True는 모든 SQL 쿼리를 콘솔에 로깅하여 디버깅에 유용합니다.
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# 세션 팩토리 생성
# autocommit=False: 트랜잭션 수동 커밋 필요
# autoflush=False: 변경 사항을 바로 DB에 플러시하지 않음 (commit 시 플러시)
# bind=engine: 생성된 엔진에 바인딩
# class_=AsyncSession: 비동기 세션 클래스 사용
# expire_on_commit=False: 커밋 후 ORM 객체가 만료되지 않도록 하여 접근 가능
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# SQLAlchemy Base 선언
# 모든 ORM 모델(예: DreamSession)은 이 Base를 상속받아야 합니다.
Base = declarative_base()

# 주의: `Base.metadata.create_all(engine)`은 동기 함수이므로,
# FastAPI lifespan 이벤트에서 `await conn.run_sync(Base.metadata.create_all)` 형태로
# 비동기적으로 실행해야 합니다. (app/main.py에 반영될 예정)