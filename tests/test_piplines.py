# my_dream_project/tests/test_pipelines.py
import pytest
from unittest.mock import AsyncMock, MagicMock # 비동기 함수를 Mocking하기 위해 AsyncMock 사용
from app.piplines.dream_pipeline import DreamPipeline
from app.services.audio_service import AudioService
from app.services.analysis_service import AnalysisService
from app.services.image_service import ImageService
from app.core.settings import settings # 설정 파일 임포트 (테스트에서 직접 사용될 일은 드뭄)
from app.utils.exceptions import ServiceException # 파이프라인에서 발생할 수 있는 예외

# ----------------------------------------------------
# Mock 객체 Fixtures
# 실제 API 호출을 Mocking하여 테스트의 안정성과 속도를 높입니다.
# 실제 API 호출을 테스트하고 싶다면 (비용 및 속도 저하 감수) Mocking 부분을 제거하세요.
# ----------------------------------------------------

@pytest.fixture
def mock_audio_service():
    """
    AudioService Mock 객체를 제공합니다.
    speech_to_text 메서드가 고정된 텍스트를 비동기적으로 반환하도록 설정합니다.
    """
    service = AsyncMock(spec=AudioService) # AudioService의 스펙을 따르는 AsyncMock 생성
    service.speech_to_text.return_value = "나는 하늘을 나는 꿈을 꾸었다. 매우 즐거웠다."
    return service

@pytest.fixture
def mock_analysis_service():
    """
    AnalysisService Mock 객체를 제공합니다.
    analyze_dream과 perform_irt 메서드가 고정된 결과를 비동기적으로 반환하도록 설정합니다.
    """
    service = AsyncMock(spec=AnalysisService)
    service.analyze_dream.return_value = {
        "summary": "하늘을 나는 즐거운 꿈",
        "keywords": ["하늘", "비행", "즐거움"],
        "symbolism_analysis": "자유와 성취감을 나타냅니다.",
        "emotional_context": "매우 긍정적입니다.",
        "potential_implications": "현실에서의 자유로운 삶을 추구할 수 있습니다.",
        "image_prompt_original": "A person joyfully flying in a surreal blue sky.",
        "image_prompt_healing": "A peaceful landscape with a gentle breeze and sun."
    }
    service.perform_irt.return_value = {
        "irt_explanation": "IRT는 꿈 이미지를 재구성하는 치료입니다.",
        "negative_elements_identified": [], # 이 테스트에서는 부정적 요소가 없다고 가정
        "rescripting_suggestions": [], # 이 테스트에서는 재구성 제안이 없다고 가정
        "actionable_insights": "꿈의 긍정적인 면을 강화하세요."
    }
    return service

@pytest.fixture
def mock_image_service():
    """
    ImageService Mock 객체를 제공합니다.
    generate_image와 generate_healing_image 메서드가 더미 URL을 비동기적으로 반환하도록 설정합니다.
    """
    service = AsyncMock(spec=ImageService)
    service.generate_image.return_value = "http://example.com/generated_image.png"
    service.generate_healing_image.return_value = "http://example.com/healing_image.png"
    return service

@pytest.fixture
def dream_pipeline(mock_audio_service, mock_analysis_service, mock_image_service):
    """
    Mock 서비스 객체들로 초기화된 DreamPipeline 인스턴스를 제공하는 fixture입니다.
    """
    return DreamPipeline(
        audio_service=mock_audio_service,
        analysis_service=mock_analysis_service,
        image_service=mock_image_service
    )

# ----------------------------------------------------
# 파이프라인 스테이지별 테스트 케이스
# ----------------------------------------------------

@pytest.mark.asyncio # 비동기 테스트 함수를 위한 마커
async def test_run_analysis_and_image_stages_success(dream_pipeline, mock_analysis_service, mock_image_service):
    """
    분석 및 이미지 생성 파이프라인 스테이지(STAGE 2, 3, 4)의 성공적인 실행을 테스트합니다.
    """
    dream_text = "꿈에서 나는 하늘을 날았다."

    # 파이프라인의 해당 스테이지 실행
    analysis_results, original_image_url, healing_image_url = await dream_pipeline.run_analysis_and_image_stages(dream_text)

    # 1. Mock 서비스 메서드가 예상대로 호출되었는지 확인
    # analysis_service의 analyze_dream 메서드가 dream_text 인자로 한 번 호출되었는지 확인
    mock_analysis_service.analyze_dream.assert_called_once_with(dream_text)
    # image_service의 generate_image 및 generate_healing_image 메서드가 각각 한 번 호출되었는지 확인
    # 이때 호출된 프롬프트는 mock_analysis_service에서 반환된 값과 일치해야 합니다.
    mock_image_service.generate_image.assert_called_once_with("A person joyfully flying in a surreal blue sky.")
    mock_image_service.generate_healing_image.assert_called_once_with("A peaceful, positive, hopeful, and healing interpretation of: A peaceful landscape with a gentle breeze and sun.")


    # 2. 파이프라인이 올바른 값을 반환했는지 확인 (Mock 객체의 return_value와 비교)
    assert analysis_results == {
        "summary": "하늘을 나는 즐거운 꿈",
        "keywords": ["하늘", "비행", "즐거움"],
        "symbolism_analysis": "자유와 성취감을 나타냅니다.",
        "emotional_context": "매우 긍정적입니다.",
        "potential_implications": "현실에서의 자유로운 삶을 추구할 수 있습니다.",
        "image_prompt_original": "A person joyfully flying in a surreal blue sky.",
        "image_prompt_healing": "A peaceful landscape with a gentle breeze and sun."
    }
    assert original_image_url == "http://example.com/generated_image.png"
    assert healing_image_url == "http://example.com/healing_image.png"

@pytest.mark.asyncio
async def test_run_irt_stage_success(dream_pipeline, mock_analysis_service):
    """
    IRT 분석 파이프라인 스테이지(STAGE 5)의 성공적인 실행을 테스트합니다.
    """
    dream_text = "꿈에서 괴물에게 쫓겼다."
    # IRT는 분석 결과를 입력으로 받으므로, 더미 분석 결과를 준비합니다.
    mock_analysis_results = {
        "summary": "괴물에게 쫓기는 꿈",
        "potential_implications": "불안감을 나타냅니다."
    }

    # 파이프라인의 IRT 스테이지 실행
    irt_results = await dream_pipeline.run_irt_stage(dream_text, mock_analysis_results)

    # 1. Mock 서비스 메서드가 예상대로 호출되었는지 확인
    # analysis_service의 perform_irt 메서드가 dream_text와 mock_analysis_results 인자로 한 번 호출되었는지 확인
    mock_analysis_service.perform_irt.assert_called_once_with(dream_text, mock_analysis_results)

    # 2. 파이프라인이 올바른 값을 반환했는지 확인 (Mock 객체의 return_value와 비교)
    assert irt_results == {
        "irt_explanation": "IRT는 꿈 이미지를 재구성하는 치료입니다.",
        "negative_elements_identified": [],
        "rescripting_suggestions": [],
        "actionable_insights": "꿈의 긍정적인 면을 강화하세요."
    }

# ----------------------------------------------------
# 예외 처리 테스트 케이스
# 서비스에서 예외 발생 시 파이프라인이 해당 예외를 올바르게 전파하는지 테스트합니다.
# ----------------------------------------------------

@pytest.mark.asyncio
async def test_analysis_stage_exception_handling(dream_pipeline, mock_analysis_service):
    """
    분석 서비스에서 ServiceException이 발생했을 때, 파이프라인이 이를 전파하는지 테스트합니다.
    """
    # analyze_dream 메서드가 ServiceException을 발생시키도록 Mock 설정
    mock_analysis_service.analyze_dream.side_effect = ServiceException("Analysis failed internally.")

    # 특정 예외가 발생할 것으로 예상되는 코드 블록을 with pytest.raises()로 감쌉니다.
    with pytest.raises(ServiceException, match="Analysis failed internally."):
        await dream_pipeline.run_analysis_and_image_stages("어떤 꿈")

@pytest.mark.asyncio
async def test_image_generation_stage_exception_handling(dream_pipeline, mock_image_service, mock_analysis_service):
    """
    이미지 생성 서비스에서 ServiceException이 발생했을 때, 파이프라인이 이를 전파하는지 테스트합니다.
    """
    # generate_image 메서드가 ServiceException을 발생시키도록 Mock 설정
    mock_image_service.generate_image.side_effect = ServiceException("Image generation failed.")
    
    # analyze_dream은 이 테스트의 초점이 아니므로 성공한다고 가정하고 return_value를 설정합니다.
    mock_analysis_service.analyze_dream.return_value = {
        "image_prompt_original": "test prompt for image",
        "image_prompt_healing": "test healing prompt for image"
    }

    # 특정 예외가 발생할 것으로 예상되는 코드 블록을 with pytest.raises()로 감쌉니다.
    with pytest.raises(ServiceException, match="Image generation failed."):
        await dream_pipeline.run_analysis_and_image_stages("다른 꿈")

@pytest.mark.asyncio
async def test_irt_stage_exception_handling(dream_pipeline, mock_analysis_service):
    """
    IRT 서비스에서 ServiceException이 발생했을 때, 파이프라인이 이를 전파하는지 테스트합니다.
    """
    # perform_irt 메서드가 ServiceException을 발생시키도록 Mock 설정
    mock_analysis_service.perform_irt.side_effect = ServiceException("IRT analysis failed internally.")
    
    # IRT는 dream_text와 analysis_results를 필요로 하므로, 더미 값을 전달합니다.
    dream_text = "IRT 실패 테스트용 꿈"
    analysis_results = {"summary": "분석 결과 더미"}

    # 특정 예외가 발생할 것으로 예상되는 코드 블록을 with pytest.raises()로 감쌉니다.
    with pytest.raises(ServiceException, match="IRT analysis failed internally."):
        await dream_pipeline.run_irt_stage(dream_text, analysis_results)
