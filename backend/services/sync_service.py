from typing import List, Dict, Any, Optional
import time
import threading
from sqlalchemy.orm import Session
from core.config import settings
from core.logger import get_logger
from services.realtime_fetch import realtime_fetch_service
from services.pipeline import run_batch_ingest_pipeline

logger = get_logger("services.sync_service")

class SyncStatus:
    def __init__(self):
        self.is_running = False
        self.current_sector = ""
        self.processed_sectors = 0
        self.total_sectors = 0
        self.last_sync_time = None
        self.error = None
        self.progress = 0

_global_sync_status = SyncStatus()

class SyncService:
    TDX_SECTORS = [
        "金融", "采掘", "化工", "钢铁", "有色", "电子", "家用电器", "食品饮料", "商业贸易", 
        "轻工制造", "医药生物", "公用事业", "交通运输", "房地产", "有色金属", "机械设备", 
        "汽车", "计算机", "传媒", "通信", "建筑装饰", "建筑材料", "电力设备", 
        "国防军工", "美容护理", "纺织服饰", "社会服务", "基础化工", "农林牧渔", "石油石化", 
        "综合", "煤炭", "非银金融", "银行"
    ]

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": _global_sync_status.is_running,
            "current_sector": _global_sync_status.current_sector,
            "processed_sectors": _global_sync_status.processed_sectors,
            "total_sectors": _global_sync_status.total_sectors,
            "last_sync_time": _global_sync_status.last_sync_time,
            "error": _global_sync_status.error,
            "progress": _global_sync_status.progress
        }

    def start_sync(self, db_factory, sector: Optional[str] = None):
        if _global_sync_status.is_running:
            return False
        
        # 验证行业是否合法
        if sector and sector not in self.TDX_SECTORS:
            raise ValueError(f"无效的行业名称: {sector}")

        _global_sync_status.is_running = True
        _global_sync_status.error = None
        _global_sync_status.processed_sectors = 0
        _global_sync_status.total_sectors = 1 if sector else len(self.TDX_SECTORS)
        _global_sync_status.progress = 0
        
        thread = threading.Thread(target=self._run_sync, args=(db_factory, sector))
        thread.daemon = True
        thread.start()
        return True

    def _run_sync(self, db_factory, target_sector: Optional[str] = None):
        try:
            sectors_to_sync = [target_sector] if target_sector else self.TDX_SECTORS
            
            for i, sector in enumerate(sectors_to_sync):
                _global_sync_status.current_sector = sector
                _global_sync_status.progress = int((i / len(sectors_to_sync)) * 100)
                
                logger.info(f"Syncing sector: {sector}")
                
                # 构造同步意图
                sync_intent = {
                    "raw_query": f"{sector}行业最近重大事件",
                    "sector": sector,
                    "market": "A股",
                    "keywords": [sector, "重大事件", "财联社电报"],
                    "prefer_cls": True,
                    "is_realtime_query": True
                }
                
                # 使用 db_factory 创建会话
                db = db_factory()
                try:
                    # 调用爬虫抓取，开启行业硬过滤
                    fetch_result = realtime_fetch_service.trigger_fallback(
                        db=db,
                        intent=sync_intent,
                        exclude_urls=set(),
                        force_sector_filter=True
                    )
                    logger.info(f"Sector {sector} sync done: {fetch_result.get('success_count', 0)} items saved")
                finally:
                    db.close()
                
                _global_sync_status.processed_sectors += 1
                # 避免请求过快被封
                time.sleep(2)
                
            _global_sync_status.progress = 100
            _global_sync_status.last_sync_time = datetime.utcnow().isoformat()
        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            _global_sync_status.error = str(e)
        finally:
            _global_sync_status.is_running = False
            _global_sync_status.current_sector = ""

from datetime import datetime
sync_service = SyncService()
