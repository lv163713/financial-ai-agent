from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from schemas.query import QueryAnalyzeResponse

class MessageBase(BaseModel):
    role: str
    content: str
    meta_data: Optional[Dict[str, Any]] = None

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    title: str = "新对话"

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []
