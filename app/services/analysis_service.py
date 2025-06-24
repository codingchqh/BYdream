# app/services/analysis_service.py
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from typing import Dict, Any, List
import json

from ..core.settings import settings # 설정 정보 로드
from ..utils.logger import get_logger # 로깅을 위해 임포트
from ..utils.exceptions import AIModelException, ServiceException # 커스텀 예외

logger = get_logger(__name__)

class AnalysisService:
    def __init__(self):
        # OpenAI 임베딩 모델 초기화 (ChromaDB 로드 및 RAG 검색에 사용)
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

        # ChromaDB 벡터 스토어 로드 (persist_directory에서 기존 DB 로드)
        # build_rag_db.py 스크립트가 먼저 실행되어 DB가 생성되어 있어야 합니다.
        self.vectorstore = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embeddings
        )
        # 리트리버 설정: 벡터 DB에서 관련 문서를 검색하는 역할
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3}) # 상위 3개 문서 검색

        # GPT-4o LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o", # 사용할 OpenAI LLM 모델
            temperature=0.7, # 창의성 조절 (0.0: 보수적, 1.0: 창의적)
            openai_api_key=settings.OPENAI_API_KEY
        )

        # ----------------------------------------------------
        # 꿈 분석을 위한 LangChain 프롬프트 정의
        # ----------------------------------------------------
        self.analysis_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """당신은 심리학 및 꿈 분석 전문가입니다. 제공된 꿈 텍스트와 관련 심리학 지식을 바탕으로 심층적인 분석을 수행합니다.
                다음 JSON 형식으로 응답해주세요:
                {
                    "summary": "꿈의 핵심 내용 요약",
                    "keywords": ["주요 키워드1", "주요 키워드2", "..."],
                    "symbolism_analysis": "꿈의 주요 상징에 대한 심리학적 해석",
                    "emotional_context": "꿈 속 감정 상태 및 의미 분석",
                    "potential_implications": "꿈이 현재 삶에 시사하는 바 또는 메시지",
                    "image_prompt_original": "이 꿈의 분위기와 핵심 요소를 담은 초현실적이거나 상징적인 이미지 생성 프롬프트 (영어)",
                    "image_prompt_healing": "이 꿈에서 느껴지는 부정적 감정을 완화하고 긍정적이고 치유적인 분위기를 담은 이미지 생성 프롬프트 (영어)"
                }
                """), # 여기 큰따옴표 바로 직전에 닫는 중괄호 '}'가 있는지 확인
                ("human", "꿈 텍스트: {dream_text}\n관련 지식: {context}")
            ]
        )

        # ----------------------------------------------------
        # IRT(Imagery Rescripting Therapy) 분석을 위한 LangChain 프롬프트 정의
        # ----------------------------------------------------
        self.irt_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """당신은 인지행동치료(CBT) 및 심상 재구성 치료(IRT) 전문가입니다. 제공된 꿈 분석 결과와 원본 꿈 텍스트를 바탕으로,
                사용자가 부정적인 꿈 이미지를 긍정적으로 재구성할 수 있도록 돕는 구체적인 가이드와 제안을 제공합니다.
                다음 JSON 형식으로 응답해주세요:
                {
                    "irt_explanation": "IRT에 대한 간략한 설명",
                    "negative_elements_identified": ["원본 꿈에서 재구성할 부정적 요소1", "..."],
                    "rescripting_suggestions": [
                        {
                            "element": "재구성할 요소",
                            "original_image": "원본 꿈 속 부정적 이미지 설명",
                            "new_image_suggestion": "새로운 긍정적 이미지에 대한 구체적인 상상 지침"
                        },
                        ...
                    ],
                    "actionable_insights": "IRT 과정을 통해 얻을 수 있는 통찰 및 실제 생활에 적용 가능한 조언"
                }
                """), # 여기도 큰따옴표 바로 직전에 닫는 중괄호 '}'가 있는지 확인
                ("human", "원본 꿈 텍스트: {dream_text}\n기존 분석 결과: {analysis_results}")
            ]
        )

        # ----------------------------------------------------
        # LangChain Chain 정의
        # ----------------------------------------------------
        # RAG를 포함한 꿈 분석 체인
        self.analysis_chain = (
            {"dream_text": RunnablePassthrough(), "context": self.retriever} # dream_text를 그대로 전달하고, retriever로 context를 가져옴
            | self.analysis_prompt
            | self.llm
            | JsonOutputParser() # LLM 응답을 JSON으로 파싱
        )

        # IRT 분석 체인
        self.irt_chain = (
            self.irt_prompt
            | self.llm
            | JsonOutputParser() # LLM 응답을 JSON으로 파싱
        )

    async def analyze_dream(self, dream_text: str) -> Dict[str, Any]:
        """
        꿈 텍스트를 분석하고 RAG를 통해 관련 심리학 지식을 통합하여 상세 분석 결과를 반환합니다.
        """
        try:
            logger.info(f"Starting dream analysis with RAG for text (first 50 chars): '{dream_text[:50]}...'")
            # LangChain Chain을 사용하여 비동기적으로 분석 수행
            response = await self.analysis_chain.ainvoke({"dream_text": dream_text})
            logger.info("Dream analysis completed successfully.")
            return response
        except Exception as e:
            logger.error(f"Error during dream analysis: {e}", exc_info=True)
            raise ServiceException(f"Failed to analyze dream: {e}")

    async def perform_irt(self, dream_text: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        주어진 꿈 텍스트와 분석 결과를 바탕으로 IRT(Imagery Rescripting Therapy) 분석을 수행합니다.
        """
        try:
            logger.info(f"Starting IRT analysis for text (first 50 chars): '{dream_text[:50]}...'")
            # analysis_results는 Dict[str, Any] 타입이므로, LLM 프롬프트에 전달하기 위해 JSON 문자열로 변환합니다.
            response = await self.irt_chain.ainvoke({"dream_text": dream_text, "analysis_results": json.dumps(analysis_results, ensure_ascii=False)})
            logger.info("IRT analysis completed successfully.")
            return response
        except Exception as e:
            logger.error(f"Error during IRT analysis: {e}", exc_info=True)
            raise ServiceException(f"Failed to perform IRT analysis: {e}")