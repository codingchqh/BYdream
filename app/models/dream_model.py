# app/models/dream_model.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON
from sqlalchemy.orm import declarative_base # SQLAlchemy 1.4+ (declarative_base)

# Base는 connection.py에서 import하여 사용하므로, 여기서 선언하지 않습니다.
# from app.database.connection import Base
# 하지만 models 폴더가 connection.py보다 먼저 임포트될 수 있으므로,
# model_base를 여기서 먼저 선언하고 connection.py에서 재할당하는 방식으로 해결합니다.
# 또는 Base를 connection.py에서만 정의하고, 여기서 import 하는 방식도 가능합니다.
# 여기서는 Base를 connection.py에서 가져오는 것으로 가정합니다.
# 임시로 여기서 Base를 정의하여 구문 에러를 피할 수 있도록 합니다.
Base = declarative_base()


class DreamSession(Base):
    __tablename__ = "dream_sessions" # 테이블 이름

    id = Column(Integer, primary_key=True, index=True) # 세션 ID (기본 키)
    dream_text = Column(Text, nullable=False) # 사용자가 말한 꿈 내용 텍스트

    # JSON 타입을 사용하여 분석 결과 저장 (DB 종류에 따라 적절한 JSON 타입 사용)
    # SQLAlchemy의 JSON 타입은 DB별로 다르게 매핑됩니다 (SQLite는 Text, PostgreSQL은 JSONB 등)
    analysis_results = Column(JSON, nullable=True)
    irt_results = Column(JSON, nullable=True)

    # 생성된 이미지 URL 목록 (JSON 배열 형태 예: [{"original": "url", "healing": "url"}])
    generated_images = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=func.now()) # 생성 시간
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) # 업데이트 시간

    # 객체 출력 시 식별 용이
    def __repr__(self):
        return f"<DreamSession(id={self.id}, dream_text='{self.dream_text[:30]}...')>"