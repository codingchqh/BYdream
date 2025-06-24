# my_dream_project/tests/test_api.py
import pytest
from httpx import AsyncClient # 비동기 테스트 클라이언트
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker # 최신 버전에서는 async_sessionmaker를 더 선호
from sqlalchemy import text # SQL 쿼리 테스트용 (여기서는 직접 사용되지 않음)
from typing import AsyncGenerator, Any # AsyncGenerator와 Any 임포트 추가

# 테스트를 위한 애플리케이션 임포트
from app.main import app
from app.core.settings import settings # 설정 정보 로드
from app.database.connection import Base # ORM Base 클래스 (테이블 생성을 위해 필요)
from app.database.session import get_db # 오버라이드할 DB 의존성 함수

# ----------------------------------------------------
# 테스트 환경을 위한 데이터베이스 설정
# ----------------------------------------------------
# 테스트용 SQLite 파일 기반 DB URL (디버깅 시 확인 용이)
# ":memory:"를 사용하면 테스트 종료 시 DB가 완전히 사라집니다.
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 테스트용 DB 엔진 생성
# echo=False로 설정하여 테스트 시 SQL 쿼리 출력을 비활성화합니다.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ----------------------------------------------------
# pytest Fixture: 테스트 시작/종료 시 DB 초기화
# ----------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """
    테스트 세션 시작 전 (setup): 테스트용 DB의 모든 테이블을 삭제하고 다시 생성합니다.
    테스트 세션 종료 후 (teardown): 모든 테이블을 다시 삭제하여 깨끗한 상태를 유지합니다.
    """
    # 테스트 시작 전 기존 테이블 삭제 및 재생성
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # 기존 테이블 모두 삭제
        await conn.run_sync(Base.metadata.create_all) # 모든 테이블 새로 생성
    yield # 이 시점에서 테스트 함수들이 실행됩니다.
    # 테스트 세션 종료 후 정리
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # 테스트 종료 후 테이블 다시 삭제


# ----------------------------------------------------
# FastAPI 의존성 오버라이드: get_db
# ----------------------------------------------------
# main.py에서 사용되는 get_db 의존성 함수를 테스트용으로 교체합니다.
# 이렇게 하면 API 호출 시 테스트용 DB 세션이 사용됩니다.
async def override_get_db() -> AsyncGenerator[AsyncSession, Any]: # <<-- 이 줄이 수정되었습니다.
    """
    테스트용 데이터베이스 세션을 제공하는 함수입니다.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        await db.close()

# FastAPI 앱의 get_db 의존성을 테스트용 override_get_db 함수로 교체합니다.
# 이는 테스트 클라이언트를 통해 앱을 호출할 때 적용됩니다.
app.dependency_overrides[get_db] = override_get_db

# ----------------------------------------------------
# API 엔드포인트 테스트 케이스들
# ----------------------------------------------------

@pytest.mark.asyncio
async def test_root_endpoint():
    """
    루트 엔드포인트("/")가 정상적으로 응답하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Welcome to My Dream Project API!" in response.json()["message"]


@pytest.mark.asyncio
async def test_create_dream_session():
    """
    새로운 꿈 분석 세션 생성 API (`/api/sessions`)를 테스트합니다.
    음성 파일을 보내면 텍스트로 변환되고 세션이 DB에 저장되는지 확인합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 테스트용 오디오 파일 바이트 데이터 (실제 Whisper API 호출은 Mocking 필요)
        # 여기서는 STT 서비스가 "dummy audio content simulating a WAV file."를 반환한다고 가정합니다.
        audio_content = b"This is a dummy audio content simulating a WAV file."
        # FastAPI의 UploadFile 형식을 모방하여 files 딕셔너리 구성
        files = {"audio_file": ("test_audio.wav", audio_content, "audio/wav")}

        response = await ac.post("/api/sessions", files=files)

    assert response.status_code == 201 # HTTP 201 Created
    assert "id" in response.json() # 'session_id' 대신 'id'로 변경됨 (dream_model.py에 맞춤)
    assert "dream_text" in response.json()
    # Mocking 없이 실제 STT 서비스가 호출된다면, 이 assert는 실제 Whisper 변환 결과에 따라 변경되어야 합니다.
    # test_pipelines.py에서와 같이 audio_service를 Mocking하는 것이 더 일반적인 방법입니다.
    # 현재는 더미 데이터를 보냈을 때 STT 서비스가 해당 더미 내용을 텍스트로 반환한다고 가정
    assert response.json()["dream_text"] == "This is a dummy audio content simulating a WAV file."

    # 생성된 세션 ID로 세션 조회 테스트
    session_id = response.json()["id"]
    async with AsyncClient(app=app, base_url="http://test") as ac:
        get_response = await ac.get(f"/api/sessions/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == session_id
    assert get_response.json()["dream_text"] == response.json()["dream_text"]


@pytest.mark.asyncio
async def test_analyze_dream_and_generate_image():
    """
    꿈 분석 및 이미지 생성 API (`/api/sessions/{session_id}/analyze`)를 테스트합니다.
    세션 생성 후 분석 요청 시, 분석 결과와 이미지 URL이 반환되는지 확인합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. 먼저 테스트용 세션을 생성합니다. (STT 결과가 있어야 분석 가능)
        # 실제 audio_service, analysis_service, image_service는 Mocking되어야 합니다.
        # 여기서는 STT가 "User's dream about flying and falling."을 반환한다고 가정
        audio_content = b"User's dream about flying and falling."
        files = {"audio_file": ("dream.wav", audio_content, "audio/wav")}
        create_session_response = await ac.post("/api/sessions", files=files)
        assert create_session_response.status_code == 201
        session_id = create_session_response.json()["id"]

        # 2. 생성된 세션 ID로 꿈 분석 요청
        response = await ac.post(f"/api/sessions/{session_id}/analyze")

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    assert "analysis_results" in response.json()
    assert "generated_image_url" in response.json()
    assert "healing_image_url" in response.json()

    # 분석 결과 내용 검증 (mocking된 analysis_service의 반환 값과 일치해야 함)
    assert "summary" in response.json()["analysis_results"]
    assert "keywords" in response.json()["analysis_results"]
    assert "http" in response.json()["generated_image_url"] # URL 형식인지 간단 확인 (http 또는 https 포함)


@pytest.mark.asyncio
async def test_perform_irt_analysis():
    """
    IRT 분석 API (`/api/sessions/{session_id}/irt`)를 테스트합니다.
    분석 결과가 있는 세션에 대해 IRT 요청 시, IRT 결과가 반환되는지 확인합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. 테스트용 세션 생성
        audio_content = b"I dreamed of being chased by a monster."
        files = {"audio_file": ("monster_dream.wav", audio_content, "audio/wav")}
        create_session_response = await ac.post("/api/sessions", files=files)
        assert create_session_response.status_code == 201
        session_id = create_session_response.json()["id"]

        # 2. 꿈 분석 (IRT 수행 전 분석 결과가 필수)
        analyze_response = await ac.post(f"/api/sessions/{session_id}/analyze")
        assert analyze_response.status_code == 200

        # 3. IRT 분석 요청
        response = await ac.post(f"/api/sessions/{session_id}/irt")

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    assert "irt_results" in response.json()
    assert "irt_explanation" in response.json()["irt_results"]
    assert "rescripting_suggestions" in response.json()["irt_results"]


@pytest.mark.asyncio
async def test_get_non_existent_session():
    """
    존재하지 않는 세션 ID로 조회 시 404 Not Found 응답이 오는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/sessions/99999") # 존재하지 않을 것으로 예상되는 ID
    assert response.status_code == 404
    assert "Session with ID 99999 not found." in response.json()["detail"]


@pytest.mark.asyncio
async def test_irt_without_analysis():
    """
    분석 없이 IRT를 요청했을 때 400 Bad Request 응답이 오는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 세션만 생성하고 analyze 단계는 건너뜁니다.
        audio_content = b"Simple dream text for IRT test."
        files = {"audio_file": ("simple.wav", audio_content, "audio/wav")}
        create_session_response = await ac.post("/api/sessions", files=files)
        assert create_session_response.status_code == 201
        session_id = create_session_response.json()["id"]

        # IRT 분석 요청
        response = await ac.post(f"/api/sessions/{session_id}/irt")
    assert response.status_code == 400
    assert "Analysis must be performed for session" in response.json()["detail"]
    assert "before IRT." in response.json()["detail"]
