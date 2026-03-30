from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from core.database import engine, Base
from core.config import settings

from api.news import router as news_router
from api.query import router as query_router
from api.jobs import router as jobs_router
from api.conversations import router as conversations_router
from api.sync import router as sync_router

# 导入所有模型，以便 SQLAlchemy 知道它们的存在
from models.news import News
from models.analysis import Analysis
from models.ingest_audit import IngestAuditLog
from models.rag_document import RagDocument
from models.daily_run_job import DailyRunJob
from models.conversation import Conversation, Message
from services.scheduler import daily_scheduler

# 创建所有表 (如果它们不存在的话)
Base.metadata.create_all(bind=engine)
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE news MODIFY content_md LONGTEXT NULL"))

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源访问，开发环境下方便调试
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)

# 注册路由
app.include_router(news_router)
app.include_router(query_router)
app.include_router(jobs_router)
app.include_router(conversations_router)
app.include_router(sync_router)


@app.on_event("startup")
def on_startup():
    daily_scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    daily_scheduler.stop()

@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "Hello, 欢迎来到金融资讯智能分析系统后端 API!",
        "docs_url": "/docs"
    }

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
