from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "金融资讯智能分析系统 API"
    VERSION: str = "1.0.0"
    
    # 数据库配置
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "12356")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "financial_agent_db")
    
    # AI 模型配置 (从环境变量读取)
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    RAG_EMBEDDING_MODEL: str = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-v3")
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "8"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.75"))
    RAG_MIN_DOCS: int = int(os.getenv("RAG_MIN_DOCS", "3"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))
    RAG_MAX_CANDIDATES: int = int(os.getenv("RAG_MAX_CANDIDATES", "300"))
    RAG_FALLBACK_MAX_URLS: int = int(os.getenv("RAG_FALLBACK_MAX_URLS", "6"))
    RAG_FALLBACK_MAX_QUERIES: int = int(os.getenv("RAG_FALLBACK_MAX_QUERIES", "3"))
    RAG_FALLBACK_TIMEOUT_SECONDS: int = int(os.getenv("RAG_FALLBACK_TIMEOUT_SECONDS", "10"))
    DAILY_JOB_URLS: str = os.getenv("DAILY_JOB_URLS", "https://example.com")
    DAILY_JOB_MAX_CONCURRENCY: int = int(os.getenv("DAILY_JOB_MAX_CONCURRENCY", "3"))
    DAILY_JOB_RETRY_TIMES: int = int(os.getenv("DAILY_JOB_RETRY_TIMES", "1"))
    DAILY_RUN_HOUR: int = int(os.getenv("DAILY_RUN_HOUR", "8"))
    DAILY_RUN_MINUTE: int = int(os.getenv("DAILY_RUN_MINUTE", "0"))
    SCHEDULER_POLL_SECONDS: int = int(os.getenv("SCHEDULER_POLL_SECONDS", "20"))
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
