# scripts/build_rag_db.py
import os
import sys
# 프로젝트 루트 디렉토리를 sys.path에 추가하여 app 모듈을 임포트할 수 있도록 합니다.
# 이 스크립트가 my_dream_project/scripts/ 폴더에서 실행된다고 가정합니다.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.settings import settings # app.core.settings에서 설정 임포트
from app.utils.logger import get_logger # app.utils.logger에서 로거 임포트

logger = get_logger(__name__)

def build_rag_database():
    """
    'data/knowledge_base' 폴더의 텍스트 문서를 읽어 ChromaDB 벡터 저장소를 구축합니다.
    """
    knowledge_base_path = "./data/knowledge_base"
    persist_directory = settings.CHROMA_DB_PATH # settings에서 ChromaDB 경로 가져옴

    # ChromaDB 저장 디렉토리가 없으면 생성
    os.makedirs(persist_directory, exist_ok=True)
    logger.info(f"Ensured ChromaDB persistence directory exists: {persist_directory}")

    if not os.path.exists(knowledge_base_path):
        logger.error(f"Knowledge base path not found: {knowledge_base_path}")
        print(f"Error: Knowledge base path not found at {os.path.abspath(knowledge_base_path)}")
        print("Please create the folder and place your psychology_corpus.txt file inside.")
        sys.exit(1) # 스크립트 종료

    documents = []
    logger.info(f"Loading documents from {knowledge_base_path}...")
    for filename in os.listdir(knowledge_base_path):
        # 숨김 파일이나 시스템 파일 (예: .DS_Store) 제외
        if filename.endswith(".txt") and not filename.startswith("."):
            file_path = os.path.join(knowledge_base_path, filename)
            logger.info(f"Attempting to load document: {file_path}")
            try:
                # encoding="utf-8"을 명시하여 인코딩 문제 방지
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
                logger.info(f"Successfully loaded {filename}.")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}", exc_info=True)
                print(f"Error loading {file_path}: {e}")

    if not documents:
        logger.warning(f"No text documents found in {knowledge_base_path}. ChromaDB will not be built.")
        print(f"Warning: No text documents found in {knowledge_base_path}. ChromaDB will not be built.")
        return

    logger.info(f"Splitting {len(documents)} documents into chunks with chunk_size={settings.RAG_CHUNK_SIZE}, chunk_overlap={settings.RAG_CHUNK_OVERLAP}...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} text chunks.")

    logger.info("Initializing OpenAI Embeddings...")
    # OpenAI API 키가 환경 변수로 설정되어 있어야 합니다.
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

    logger.info(f"Creating or loading ChromaDB vector store at {persist_directory}...")
    # Chroma.from_documents는 문서를 임베딩하고 persist_directory에 저장합니다.
    # 만약 해당 디렉토리에 기존 DB가 있다면 로드하고, 없다면 새로 생성합니다.
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    # from_documents를 사용하면 내부적으로 persist()가 호출될 수 있지만, 명시적으로 호출하는 것이 안전합니다.
    vectorstore.persist()
    logger.info("ChromaDB vector store built successfully!")
    print(f"\nChromaDB vector store successfully built at {os.path.abspath(persist_directory)}\n")

if __name__ == "__main__":
    # 스크립트 실행 전에 OPENAI_API_KEY가 환경 변수로 설정되어 있어야 합니다.
    # 예: export OPENAI_API_KEY="your_key" (Linux/macOS)
    #     set OPENAI_API_KEY="your_key" (Windows CMD)
    #     $env:OPENAI_API_KEY="your_key" (Windows PowerShell)
    
    # settings 객체를 로드하기 위해 환경 변수가 필요합니다.
    if not settings.OPENAI_API_KEY:
        print("CRITICAL ERROR: OPENAI_API_KEY environment variable is not set. Please set it before running this script.")
        sys.exit(1)

    print("--- Starting RAG Database Build ---")
    try:
        build_rag_database()
    except Exception as e:
        logger.critical(f"Failed to build RAG database: {e}", exc_info=True)
        print(f"CRITICAL ERROR: Failed to build RAG database. Please check logs for details: {e}")
        sys.exit(1)
    print("--- RAG Database Build Finished ---")