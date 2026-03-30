from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.sync_service import sync_service

router = APIRouter(prefix="/sync", tags=["sync"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from pydantic import BaseModel

class SyncRequest(BaseModel):
    sector: Optional[str] = None

@router.post("/start")
def start_sync(payload: Optional[SyncRequest] = None):
    """开始行业同步任务，支持指定单个行业或全行业同步"""
    sector = payload.sector if payload else None
    try:
        success = sync_service.start_sync(SessionLocal, sector=sector)
        if not success:
            raise HTTPException(status_code=400, detail="同步任务已在运行中")
        return {"status": "success", "message": f"{sector or '全行业'}同步任务已启动"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
def get_sync_status():
    """获取同步任务状态"""
    return sync_service.get_status()
