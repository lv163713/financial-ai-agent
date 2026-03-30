from urllib.parse import urlparse
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.news import News
from models.analysis import Analysis
from models.ingest_audit import IngestAuditLog
from services.scraper import jina_reader
from services.ai_agent import ai_analyzer
from services.vector_store import vector_store
from services.metrics import metrics_store
from core.logger import get_logger

logger = get_logger("services.pipeline")


def extract_title(markdown_content: str, target_url: str) -> str:
    for line in markdown_content.splitlines():
        if line.startswith("Title:"):
            value = line.replace("Title:", "", 1).strip()
            if value:
                return value[:255]
    return target_url[:255]


def extract_source(target_url: str, explicit_source: Optional[str]) -> str:
    if explicit_source:
        return explicit_source
    domain = urlparse(target_url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain or "unknown"


def _fetch_and_analyze(target_url: str, source: Optional[str] = None, required_sector: Optional[str] = None) -> Dict[str, Any]:
    markdown_content = jina_reader.fetch_markdown(target_url)
    if not markdown_content:
        raise ValueError("网页抓取失败，未获取到正文内容")

    title = extract_title(markdown_content, target_url)
    source_name = extract_source(target_url, source)
    ai_result = ai_analyzer.analyze_news(markdown_content)
    
    # 行业相关性硬过滤
    if required_sector:
        affected_sectors = str(ai_result.get("affected_sectors", "")).lower()
        summary = str(ai_result.get("summary", "")).lower()
        sector_lc = required_sector.lower()
        
        if sector_lc not in affected_sectors and sector_lc not in summary and sector_lc not in title.lower():
            logger.warning(f"Sector mismatch: required {required_sector}, but got {affected_sectors}. URL: {target_url}")
            raise ValueError(f"资讯内容与行业 {required_sector} 不相关，已自动过滤")

    return {
        "title": title,
        "target_url": target_url,
        "source_name": source_name,
        "markdown_content": markdown_content,
        "ai_result": ai_result
    }


def _save_ingest_result(
    db: Session,
    target_url: str,
    title: str,
    source_name: str,
    markdown_content: str,
    ai_result: Dict[str, Any]
) -> dict:
    summary = ai_result.get("summary", "分析失败")
    impact_assessment = ai_result.get("impact_assessment", "中性")
    affected_sectors = ai_result.get("affected_sectors", "未知")
    logical_reasoning = ai_result.get("logical_reasoning", "")

    news = db.query(News).filter(News.url == target_url).first()
    if news is None:
        news = News(
            title=title,
            url=target_url,
            source=source_name,
            content_md=markdown_content
        )
        db.add(news)
        db.flush()
    else:
        news.title = title
        news.source = source_name
        news.content_md = markdown_content

    analysis = db.query(Analysis).filter(Analysis.news_id == news.id).first()
    if analysis is None:
        analysis = Analysis(
            news_id=news.id,
            summary=summary,
            impact_assessment=impact_assessment,
            affected_sectors=affected_sectors,
            logical_reasoning=logical_reasoning
        )
        db.add(analysis)
    else:
        analysis.summary = summary
        analysis.impact_assessment = impact_assessment
        analysis.affected_sectors = affected_sectors
        analysis.logical_reasoning = logical_reasoning

    try:
        db.commit()
        db.refresh(news)
        db.refresh(analysis)
    except Exception:
        db.rollback()
        raise

    try:
        vector_store.upsert_news_document(
            db=db,
            news_id=news.id,
            content=news.content_md or "",
            source=news.source,
            market=None,
            sectors=analysis.affected_sectors,
            published_at=news.publish_time or news.created_at
        )
    except Exception:
        db.rollback()
        logger.warning(f"vector_upsert_failed news_id={news.id}")

    return {
        "news_id": news.id,
        "title": news.title,
        "url": news.url,
        "source": news.source,
        "summary": analysis.summary,
        "impact_assessment": analysis.impact_assessment,
        "affected_sectors": analysis.affected_sectors or "",
        "logical_reasoning": analysis.logical_reasoning or ""
    }


def _fetch_and_analyze_with_retry(
    target_url: str,
    source: Optional[str],
    retry_times: int,
    required_sector: Optional[str] = None
) -> Dict[str, Any]:
    last_error = ""
    for attempt in range(retry_times + 1):
        try:
            stage_result = _fetch_and_analyze(
                target_url=target_url, 
                source=source, 
                required_sector=required_sector
            )
            stage_result["retry_count"] = attempt
            return stage_result
        except Exception as e:
            last_error = str(e)
    raise ValueError(f"{last_error}（已重试{retry_times}次）")


def _write_audit_log(
    db: Session,
    url: str,
    source: Optional[str],
    success: bool,
    retry_count: int,
    error_message: Optional[str],
    news_id: Optional[int],
    started_at: datetime,
    finished_at: datetime
) -> int:
    audit_log = IngestAuditLog(
        url=url,
        source=source,
        success=success,
        retry_count=retry_count,
        error_message=error_message,
        news_id=news_id,
        started_at=started_at,
        finished_at=finished_at
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log.id


def run_ingest_pipeline(db: Session, target_url: str, source: Optional[str] = None) -> dict:
    stage_result = _fetch_and_analyze(target_url=target_url, source=source)
    return _save_ingest_result(db=db, **stage_result)


def run_batch_ingest_pipeline(
    db: Session,
    items: List[Dict[str, Optional[str]]],
    max_concurrency: int = 3,
    retry_times: int = 1
) -> dict:
    total = len(items)
    results: List[Dict[str, Any]] = [{} for _ in range(total)]
    futures = {}
    started_times: Dict[int, datetime] = {}

    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        for index, item in enumerate(items):
            target_url = item["url"]
            source = item.get("source")
            required_sector = item.get("required_sector")
            started_times[index] = datetime.utcnow()
            future = executor.submit(
                _fetch_and_analyze_with_retry, 
                target_url, 
                source, 
                retry_times, 
                required_sector
            )
            futures[future] = (index, target_url, source)

        for future in as_completed(futures):
            index, target_url, source = futures[future]
            started_at = started_times[index]
            finished_at = datetime.utcnow()
            try:
                stage_result = future.result()
                retry_count = int(stage_result.pop("retry_count", 0))
                saved = _save_ingest_result(db=db, **stage_result)
                audit_log_id = _write_audit_log(
                    db=db,
                    url=target_url,
                    source=source,
                    success=True,
                    retry_count=retry_count,
                    error_message=None,
                    news_id=saved["news_id"],
                    started_at=started_at,
                    finished_at=finished_at
                )
                results[index] = {
                    "url": target_url,
                    "success": True,
                    "retry_count": retry_count,
                    "audit_log_id": audit_log_id,
                    "error": None,
                    **saved
                }
            except Exception as e:
                db.rollback()
                error_message = str(e)
                audit_log_id = _write_audit_log(
                    db=db,
                    url=target_url,
                    source=source,
                    success=False,
                    retry_count=retry_times,
                    error_message=error_message,
                    news_id=None,
                    started_at=started_at,
                    finished_at=finished_at
                )
                results[index] = {
                    "url": target_url,
                    "success": False,
                    "retry_count": retry_times,
                    "audit_log_id": audit_log_id,
                    "error": error_message,
                    "news_id": None,
                    "title": None,
                    "source": None,
                    "summary": None,
                    "impact_assessment": None,
                    "affected_sectors": None,
                    "logical_reasoning": None
                }

    success_count = sum(1 for item in results if item.get("success"))
    failed_count = total - success_count
    metrics_store.record_ingest_batch(total=total, success_count=success_count, failed_count=failed_count)
    return {
        "total": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results
    }
