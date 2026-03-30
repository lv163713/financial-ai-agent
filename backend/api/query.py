from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time
from core.database import get_db
from schemas.query import QueryAnalyzeRequest, QueryAnalyzeResponse
from services.query_workflow import run_query_workflow
from models.conversation import Conversation, Message


router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/analyze", response_model=QueryAnalyzeResponse, summary="查询财经主题并返回结构化分析")
def analyze_query(payload: QueryAnalyzeRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        result_dict = run_query_workflow(
            db=db,
            query=payload.query,
            market=payload.market,
            time_range_hours=payload.time_range_hours
        )
        
        # 计算耗时
        processing_ms = int((time.time() - start_time) * 1000)
        
        # 处理返回结果，确保它是 QueryAnalyzeResponse 模型或将其转换
        if isinstance(result_dict, dict):
            if "meta" in result_dict:
                result_dict["meta"]["processing_ms"] = processing_ms
            else:
                result_dict["meta"] = {"processing_ms": processing_ms}
            result = QueryAnalyzeResponse(**result_dict)
        else:
            if hasattr(result_dict, "meta") and result_dict.meta:
                result_dict.meta.processing_ms = processing_ms
            result = result_dict
            
        # 如果有会话 ID，保存到数据库
        if payload.conversation_id:
            # 1. 保存用户的提问
            user_msg = Message(
                conversation_id=payload.conversation_id,
                role="user",
                content=payload.query
            )
            db.add(user_msg)
            
            # 2. 保存 AI 的回答及完整元数据
            bot_msg = Message(
                conversation_id=payload.conversation_id,
                role="assistant",
                content=result.analysis.summary, # 存一个纯文本摘要作为内容
                meta_data=result.model_dump()    # 存下完整的 JSON 数据供前端渲染
            )
            db.add(bot_msg)
            
            # 3. 如果会话标题是"新对话"，用用户的提问作为标题
            conv = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
            if conv and conv.title == "新对话":
                conv.title = payload.query[:20] + ("..." if len(payload.query) > 20 else "")
                
            db.commit()

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
