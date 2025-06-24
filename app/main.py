# app/main.py
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager # 애플리케이션 라이프사이클 관리
from .api.dream_routes import router as dream_router # API 라우터 임포트
from .core.settings import settings # 설정 임포트
from .database.connection import engine, Base # DB 엔진 및 Base 임포트
from .utils.logger import get_logger # 로거 임포트
from .utils.exceptions import ServiceException # 커스텀 예외 임포트

logger = get_logger(__name__)

# ----------------------------------------------------
# FastAPI 애플리케이션 라이프사이클 이벤트 (시작/종료)
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작 시 DB 테이블 생성 및 초기화 작업을 수행합니다.
    애플리케이션 종료 시 정리 작업을 수행합니다.
    """
    # 1. DB 테이블 생성
    logger.info("Application lifespan: Starting up...")
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    try:
        async with engine.begin() as conn:
            # Base.metadata.create_all은 동기 함수이므로 run_sync를 사용하여 비동기 컨텍스트에서 실행
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/checked successfully.")
    except Exception as e:
        logger.critical(f"Failed to connect to database or create tables: {e}", exc_info=True)
        # DB 연결 실패 시 앱 시작을 막을 수 있음 (배포 환경에서 중요)
        # raise RuntimeError(f"Database initialization failed: {e}")

    yield # 애플리케이션이 실행되는 동안

    # 2. 애플리케이션 종료 시 정리 작업 (예: DB 연결 풀 정리 등)
    logger.info("Application lifespan: Shutting down...")
    # SQLAlchemy 엔진은 보통 애플리케이션 종료 시 자동으로 연결을 정리합니다.
    # 명시적으로 close()를 호출할 필요는 없지만, 필요한 경우 추가할 수 있습니다.
    # await engine.dispose()
    logger.info("Application shutdown completed.")

# ----------------------------------------------------
# FastAPI 애플리케이션 인스턴스 생성
# ----------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="My Dream Project API for dream analysis and interpretation using LLMs and RAG.",
    lifespan=lifespan, # lifespan 이벤트 추가
)

# ----------------------------------------------------
# 전역 예외 핸들러 등록
# ----------------------------------------------------
# ServiceException을 FastAPI의 HTTPException으로 변환하여 일관된 응답 제공
@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    logger.error(f"Service Exception caught: {exc.status_code} - {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(f"Unhandled Exception caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# ----------------------------------------------------
# API 라우터 포함
# ----------------------------------------------------
app.include_router(dream_router, prefix="/api") # /api/{endpoint} 형태로 접근

# ----------------------------------------------------
# 루트 엔드포인트
# ----------------------------------------------------
@app.get("/", summary="API 헬스 체크 및 환영 메시지")
async def root():
    """
    API의 기본 헬스 체크 엔드포인트입니다.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME} API! Go to /docs for API documentation."}

# 이 부분은 Uvicorn으로 실행할 때 직접 호출되지 않습니다.
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)