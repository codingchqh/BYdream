# app/utils/exceptions.py

class ServiceException(Exception):
    """
    서비스 계층에서 발생하는 일반적인 예외를 위한 커스텀 예외 클래스.
    FastAPI의 HTTPException과 연동하여 사용될 수 있습니다.
    """
    def __init__(self, message: str = "Service operation failed", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(ServiceException):
    """
    리소스를 찾을 수 없을 때 발생하는 예외 (HTTP 404).
    """
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class BadRequestException(ServiceException):
    """
    잘못된 요청 파라미터나 상태로 인해 발생하는 예외 (HTTP 400).
    """
    def __init__(self, message: str = "Bad request"):
        super().__init__(message, status_code=400)

class AIModelException(ServiceException):
    """
    AI 모델 (OpenAI 등)과의 통신 또는 응답 처리 중 발생하는 예외.
    """
    def __init__(self, message: str = "AI model error"):
        super().__init__(message, status_code=500)

# 필요한 다른 커스텀 예외들을 여기에 추가할 수 있습니다.