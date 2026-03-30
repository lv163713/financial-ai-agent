from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models.news import News
from schemas.news import NewsCreate, NewsResponse
from schemas.pipeline import (
    PipelineRequest,
    PipelineResponse,
    BatchPipelineRequest,
    BatchPipelineResponse
)
from services.pipeline import run_ingest_pipeline, run_batch_ingest_pipeline
from typing import List

router = APIRouter(prefix="/news", tags=["News"])

@router.post("/", response_model=NewsResponse, summary="添加一条测试新闻")
def create_news(news_in: NewsCreate, db: Session = Depends(get_db)):
    # 检查URL是否已存在
    db_news = db.query(News).filter(News.url == news_in.url).first()
    if db_news:
        raise HTTPException(status_code=400, detail="该新闻URL已存在数据库中")
    
    # 创建新记录
    new_item = News(
        title=news_in.title,
        url=news_in.url,
        source=news_in.source,
        content_md=news_in.content_md
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/", response_model=List[NewsResponse], summary="获取新闻列表")
def get_news_list(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    news_list = db.query(News).offset(skip).limit(limit).all()
    return news_list


@router.post("/ingest", response_model=PipelineResponse, summary="抓取新闻并完成AI分析后入库")
def ingest_news(payload: PipelineRequest, db: Session = Depends(get_db)):
    try:
        result = run_ingest_pipeline(db=db, target_url=str(payload.url), source=payload.source)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/ingest/batch", response_model=BatchPipelineResponse, summary="批量抓取新闻并完成AI分析后入库")
def batch_ingest_news(payload: BatchPipelineRequest, db: Session = Depends(get_db)):
    try:
        items = [{"url": str(item.url), "source": item.source} for item in payload.items]
        result = run_batch_ingest_pipeline(
            db=db,
            items=items,
            max_concurrency=payload.max_concurrency,
            retry_times=payload.retry_times
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
