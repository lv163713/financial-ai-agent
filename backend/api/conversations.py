from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from models.conversation import Conversation, Message
from schemas.conversation import ConversationResponse, ConversationCreate, ConversationDetailResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationResponse])
def get_conversations(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """获取会话列表，按更新时间倒序"""
    conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations

@router.post("", response_model=ConversationResponse)
def create_conversation(data: ConversationCreate, db: Session = Depends(get_db)):
    """创建一个新会话"""
    db_conv = Conversation(title=data.title)
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """获取特定会话的详细信息及历史消息"""
    db_conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not db_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return db_conv

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """删除特定会话及其所有消息"""
    db_conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not db_conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(db_conv)
    db.commit()
    return {"message": "success"}
