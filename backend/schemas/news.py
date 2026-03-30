from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 请求：创建新闻时的数据结构
class NewsCreate(BaseModel):
    title: str
    url: str
    source: Optional[str] = None
    content_md: Optional[str] = None

# 响应：返回新闻时的数据结构
class NewsResponse(BaseModel):
    id: int
    title: str
    url: str
    source: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 SQLAlchemy 模型转换