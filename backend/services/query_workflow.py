import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.news import News
from models.analysis import Analysis
from services.intent_parser import intent_parser
from services.vector_store import vector_store
from services.realtime_fetch import realtime_fetch_service
from services.metrics import metrics_store
from core.logger import get_logger
from core.config import settings

logger = get_logger("services.query_workflow")


def run_query_workflow(db: Session, query: str, market: Optional[str] = None, time_range_hours: Optional[int] = None) -> Dict[str, Any]:
    started = time.time()
    intent = intent_parser.parse_intent(query=query, market=market, time_range_hours=time_range_hours or 24)
    matched_items = _search_recent_items(db=db, intent=intent)
    matched_items = _filter_relevant_items(intent=intent, items=matched_items)

    # 优化触发逻辑：结合意图时效性和数据新鲜度
    is_realtime = intent.get("is_realtime_query", False)
    time_window_hours = intent.get("time_range_hours", 24)
    
    has_recent_data = False
    last_update_time = None
    if matched_items:
        # 获取最晚的更新时间
        last_update_time = max([item["news"].created_at for item in matched_items if item["news"].created_at])
        
        # 如果是实时需求，检查是否有最近 12 小时内的资料
        # 如果是普通需求（如 60 天），检查是否有最近 7 天内的资料作为基准
        freshness_threshold = 12 if is_realtime else (24 * 7) 
        if last_update_time >= datetime.utcnow() - timedelta(hours=freshness_threshold):
            has_recent_data = True

    # 修改：不再自动触发爬虫，而是改为标记建议更新
    needs_sync = False
    sync_reason = None
    
    if len(matched_items) < settings.RAG_MIN_DOCS:
        needs_sync = True
        sync_reason = "data_missing"
    elif is_realtime and not has_recent_data:
        needs_sync = True
        sync_reason = "outdated"

    fallback_meta = {
        "attempted": False,
        "search_queries": [],
        "candidate_urls": [],
        "success_count": 0,
        "failed_count": 0,
        "needs_sync": needs_sync,
        "sync_reason": sync_reason,
        "last_sync_time": last_update_time.isoformat() if last_update_time else None
    }
    
    # 彻底移除自动爬取逻辑
    fallback_triggered = False

    analysis = _build_analysis(intent=intent, matched_items=matched_items, fallback_triggered=fallback_triggered)
    
    # 新增：反思校验 (Reflection) - 检查生成的分析内容是否与意图板块冲突
    analysis_quality = _check_analysis_relevance(intent=intent, analysis=analysis, matched_items=matched_items)
    
    # 如果反思发现不匹配，也不再强制触发爬虫，而是直接应用拦截提示
    if not analysis_quality["is_relevant"]:
        analysis = _apply_relevance_interception(intent=intent, analysis=analysis, matched_items=matched_items)
        fallback_meta["needs_sync"] = True
    
    evidence = [_to_evidence_item(item) for item in matched_items[:5]]
    quality = _validate_output_quality(intent=intent, analysis=analysis, evidence=evidence)
    processing_ms = int((time.time() - started) * 1000)
    metrics_store.record_query(
        processing_ms=processing_ms,
        fallback_attempted=bool(fallback_meta["attempted"]),
        quality_passed=quality["quality_passed"]
    )
    if not quality["quality_passed"]:
        logger.warning(f"query_quality_failed issues={quality['quality_issues']}")
    return {
        "intent": intent,
        "evidence": evidence,
        "analysis": analysis,
        "meta": {
            "retrieved_count": len(matched_items),
            "fallback_triggered": fallback_triggered,
            "fallback_attempted": fallback_meta["attempted"],
            "fallback_success_count": fallback_meta["success_count"],
            "fallback_failed_count": fallback_meta["failed_count"],
            "fallback_candidate_count": len(fallback_meta.get("candidate_urls", [])),
            "fallback_search_queries": fallback_meta.get("search_queries", []),
            "needs_sync": fallback_meta.get("needs_sync", False),
            "sync_reason": fallback_meta.get("sync_reason"),
            "last_sync_time": fallback_meta.get("last_sync_time"),
            "quality_passed": quality["quality_passed"],
            "quality_issues": quality["quality_issues"],
            "field_completeness_rate": quality["field_completeness_rate"],
            "evidence_freshness_passed": quality["evidence_freshness_passed"],
            "processing_ms": processing_ms
        }
    }


def _search_recent_items(db: Session, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    vector_items = _search_recent_items_by_vector(db=db, intent=intent)
    if len(vector_items) >= settings.RAG_MIN_DOCS:
        return vector_items
    keyword_items = _search_recent_items_by_keyword(db=db, intent=intent)
    merged = _merge_scored_items(vector_items, keyword_items)
    return merged


def _search_recent_items_by_vector(db: Session, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    query_text = _build_query_text(intent)
    try:
        hits = vector_store.search(
            db=db,
            query_text=query_text,
            market=intent.get("market"),
            time_range_hours=intent["time_range_hours"],
            top_k=max(settings.RAG_TOP_K, settings.RAG_MIN_DOCS)
        )
    except Exception:
        return []
    if not hits:
        return []
    by_news_id: Dict[int, float] = {}
    for hit in hits:
        score = float(hit.get("score", 0.0))
        if score < settings.RAG_SIMILARITY_THRESHOLD:
            continue
        news_id = int(hit["news_id"])
        if news_id not in by_news_id or score > by_news_id[news_id]:
            by_news_id[news_id] = score
    if not by_news_id:
        return []
    rows = (
        db.query(News, Analysis)
        .outerjoin(Analysis, Analysis.news_id == News.id)
        .filter(News.id.in_(list(by_news_id.keys())))
        .all()
    )
    results: List[Dict[str, Any]] = []
    prefer_cls = intent.get("prefer_cls", False)
    for news, analysis in rows:
        similarity_score = round(by_news_id.get(news.id, 0.0), 4)
        # 如果是重大事件且来源是财联社，给予权重分值加成
        if prefer_cls and news.source and ("cls" in news.source.lower() or "财联社" in news.source):
            similarity_score = min(1.0, similarity_score + 0.1)
            
        results.append(
            {
                "news": news,
                "analysis": analysis,
                "similarity_score": similarity_score
            }
        )
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results


def _search_recent_items_by_keyword(db: Session, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    time_window = datetime.utcnow() - timedelta(hours=intent["time_range_hours"])
    rows = (
        db.query(News, Analysis)
        .outerjoin(Analysis, Analysis.news_id == News.id)
        .filter(News.created_at >= time_window)
        .order_by(News.created_at.desc())
        .limit(200)
        .all()
    )
    keywords = intent.get("keywords", [])
    sector = intent.get("sector")
    if sector and sector not in keywords:
        keywords = [sector] + keywords
    scored: List[Dict[str, Any]] = []
    for news, analysis in rows:
        text_parts = [news.title or "", news.content_md or ""]
        if analysis:
            text_parts.extend([
                analysis.summary or "",
                analysis.affected_sectors or "",
                analysis.logical_reasoning or ""
            ])
        text = " ".join(text_parts).lower()
        hit_count = sum(1 for kw in keywords if kw.lower() in text)
        if hit_count == 0:
            continue
        recency_bonus = 0.2 if news.created_at and news.created_at >= datetime.utcnow() - timedelta(hours=24) else 0.0
        similarity_score = min(1.0, 0.5 + hit_count * 0.1 + recency_bonus)
        
        # 财联社电报加成
        if intent.get("prefer_cls") and news.source and ("cls" in news.source.lower() or "财联社" in news.source):
            similarity_score = min(1.0, similarity_score + 0.15)
            
        scored.append({
            "news": news,
            "analysis": analysis,
            "similarity_score": round(similarity_score, 4)
        })
    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored


def _build_query_text(intent: Dict[str, Any]) -> str:
    parts = [intent.get("raw_query", "")]
    keywords = intent.get("keywords", [])
    if keywords:
        parts.append(" ".join(keywords))
    if intent.get("sector"):
        parts.append(str(intent["sector"]))
    if intent.get("market"):
        parts.append(str(intent["market"]))
    return " ".join(part for part in parts if part).strip()


def _merge_scored_items(primary: List[Dict[str, Any]], secondary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[int, Dict[str, Any]] = {}
    for item in primary + secondary:
        news = item["news"]
        current = merged.get(news.id)
        if current is None or item["similarity_score"] > current["similarity_score"]:
            merged[news.id] = item
    items = list(merged.values())
    items.sort(key=lambda x: x["similarity_score"], reverse=True)
    return items


def _filter_relevant_items(intent: Dict[str, Any], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sector = (intent.get("sector") or "").strip()
    keywords = intent.get("keywords", [])
    market = intent.get("market")
    
    if not sector and not keywords and (not market or market == "全球"):
        return items

    sector_lc = sector.lower() if sector else None
    keywords_lc = [kw.lower() for kw in keywords]
    market_val = market
    
    filtered: List[Dict[str, Any]] = []
    for item in items:
        analysis = item.get("analysis")
        news = item.get("news")
        if not news:
            continue
            
        # 0. 市场硬性过滤 (Market Strict Filter)
        if market_val and market_val != "全球":
            news_market = getattr(news, "market", "全球")
            # 如果新闻明确标注了市场，且与意图不符，直接剔除
            if news_market and news_market != "全球" and news_market != market_val:
                continue

        ok = False
        # 1. 优先板块匹配
        if sector_lc:
            if analysis and analysis.affected_sectors:
                if sector_lc in str(analysis.affected_sectors).lower():
                    ok = True
            if not ok:
                title = (news.title or "").lower()
                body = (news.content_md or "")[:2000].lower()
                if sector_lc in title or sector_lc in body:
                    ok = True
        
        # 2. 如果板块没中，但关键词命中且相似度较高，也算匹配
        if not ok and keywords_lc:
            title = (news.title or "").lower()
            body = (news.content_md or "")[:1000].lower()
            # 至少命中一个关键词，且分值不能太低
            if any(kw in title or kw in body for kw in keywords_lc):
                if item.get("similarity_score", 0) >= 0.7:
                    ok = True
        
        # 3. 严格逻辑：移除原有的 0.9 分强制放行逻辑，防止“半导体”匹配到“猪肉”
        # 除非确实没有任何板块信息可以参考
        if not ok and not sector_lc and not keywords_lc:
            if item.get("similarity_score", 0) >= 0.85:
                ok = True
                
        if ok:
            filtered.append(item)
    return filtered


def _run_fallback_fetch(db: Session, intent: Dict[str, Any], matched_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    existing_urls = set()
    for item in matched_items:
        news = item.get("news")
        if news and getattr(news, "url", None):
            existing_urls.add(news.url)
    try:
        return realtime_fetch_service.trigger_fallback(
            db=db,
            intent=intent,
            exclude_urls=existing_urls
        )
    except Exception:
        return {
            "attempted": True,
            "search_queries": [],
            "candidate_urls": [],
            "success_count": 0,
            "failed_count": 0,
            "results": []
        }


def _to_evidence_item(item: Dict[str, Any]) -> Dict[str, Any]:
    news = item["news"]
    return {
        "source": news.source or "unknown",
        "url": news.url,
        "title": news.title,
        "published_at": news.created_at.isoformat() if news.created_at else None,
        "similarity_score": item["similarity_score"]
    }


def _build_analysis(intent: Dict[str, Any], matched_items: List[Dict[str, Any]], fallback_triggered: bool) -> Dict[str, Any]:
    if not matched_items:
        return {
            "summary": "当前时间窗口内未命中足够资讯。",
            "impact_assessment": "中性",
            "affected_sectors": intent.get("sector") or "未知",
            "logical_reasoning": "现有数据库中可检索内容不足，建议触发实时抓取补充数据后再判断市场影响。",
            "risk_notice": "当前结果基于存量数据，时效性或覆盖度不足。"
        }

    analysis_items = [item["analysis"] for item in matched_items if item["analysis"] is not None]
    if analysis_items:
        latest = analysis_items[0]
        summary = latest.summary or "已找到近期相关资讯。"
        impact_assessment = latest.impact_assessment or "中性"
        affected_sectors = latest.affected_sectors or (intent.get("sector") or "未知")
        logical_reasoning = latest.logical_reasoning or "基于近期资讯聚合判断。"
    else:
        summary = "已命中近期资讯，但分析数据尚不完整。"
        impact_assessment = "中性"
        affected_sectors = intent.get("sector") or "未知"
        logical_reasoning = "命中结果主要来自新闻正文关键词匹配。"

    risk_notice = "检索命中不足，建议触发实时抓取补全后复核。" if fallback_triggered else "结果基于近期命中资讯生成，请结合多源信息复核。"
    return {
        "summary": summary,
        "impact_assessment": impact_assessment,
        "affected_sectors": affected_sectors,
        "logical_reasoning": logical_reasoning,
        "risk_notice": risk_notice
    }


def _check_analysis_relevance(intent: Dict[str, Any], analysis: Dict[str, Any], matched_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    检查生成的分析内容是否与用户请求的板块和市场匹配。
    """
    sector = intent.get("sector")
    keywords = intent.get("keywords", [])
    market = intent.get("market")
    
    summary = analysis.get("summary", "")
    affected_sectors = str(analysis.get("affected_sectors", ""))
    
    # 1. 市场一致性校验 (Market Consistency Check)
    if market and market != "全球":
        # 如果意图是 A股，但分析摘要大谈特谈美股，则判定不相关
        if market == "A股" and ("美股" in summary or "纳斯达克" in summary) and "A股" not in summary:
            return {"is_relevant": False, "reason": "market_mismatch"}

    # 2. 板块/关键词一致性校验 (Sector/Keywords Consistency Check)
    if sector or keywords:
        content_to_check = (summary + affected_sectors).lower()
        
        # 只要命中行业分类词 或者 命中原始关键词中的任意一个，就认为相关
        matched_any = False
        if sector and sector.lower() in content_to_check:
            matched_any = True
        
        if not matched_any and keywords:
            # 过滤掉过于笼统的词，避免误判
            black_list = {"a股", "影响", "市场", "行业", "板块", "分析", "追踪", "资讯", "新闻"}
            meaningful_keywords = [kw for kw in keywords if kw.lower() not in black_list]
            
            for kw in (meaningful_keywords if meaningful_keywords else keywords):
                if kw.lower() in content_to_check:
                    matched_any = True
                    break
        
        if not matched_any:
            # 最后的倔强：检查检索出的新闻标题
            if matched_items:
                first_item_news = matched_items[0]["news"]
                first_title = (first_item_news.title or "").lower()
                first_content = (first_item_news.content_md or "").lower()[:500]
                
                # 同样使用过滤后的关键词
                black_list = {"a股", "影响", "市场", "行业", "板块", "分析", "追踪", "资讯", "新闻"}
                meaningful_keywords = [kw for kw in keywords if kw.lower() not in black_list]
                target_kws = meaningful_keywords if meaningful_keywords else keywords

                # 如果标题或正文开头命中了关键词，也算过
                if (sector and sector.lower() in first_title) or any(kw.lower() in first_title for kw in target_kws):
                    matched_any = True
                elif any(kw.lower() in first_content for kw in target_kws):
                    matched_any = True
            
            if not matched_any:
                return {"is_relevant": False, "reason": "sector_mismatch"}
    
    return {"is_relevant": True}


def _apply_relevance_interception(intent: Dict[str, Any], analysis: Dict[str, Any], matched_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    应用拦截处理，当内容不匹配时返回提示性信息。
    """
    sector = intent.get("sector", "相关")
    raw_query = intent.get("raw_query", "")
    target = sector if sector != "相关" else "该主题"
    
    affected_sectors = str(analysis.get("affected_sectors", "其他板块"))
    
    return {
        "summary": f"抱歉，关于 {target} 的最新精准资讯检索受限。",
        "impact_assessment": "未知",
        "affected_sectors": target,
        "logical_reasoning": f"系统检索到的资料主要涉及 {affected_sectors}，与您请求的“{raw_query}”意图不完全匹配，已自动拦截可能存在的偏差输出。",
        "risk_notice": "请尝试调整提问方式，例如直接询问具体的股票或更细分的行业关键词。"
    }


def _validate_output_quality(intent: Dict[str, Any], analysis: Dict[str, Any], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    required_fields = ["summary", "impact_assessment", "affected_sectors", "logical_reasoning", "risk_notice"]
    filled = 0
    for field in required_fields:
        value = str(analysis.get(field, "")).strip()
        if value:
            filled += 1
    field_completeness_rate = round(filled / len(required_fields), 4)
    time_range_hours = int(intent.get("time_range_hours", 24))
    freshness_boundary = datetime.utcnow() - timedelta(hours=time_range_hours)
    freshness_passed = True
    for item in evidence:
        published_at = item.get("published_at")
        if not published_at:
            continue
        try:
            published_dt = datetime.fromisoformat(str(published_at))
            if published_dt < freshness_boundary:
                freshness_passed = False
                break
        except Exception:
            freshness_passed = False
            break
    issues: List[str] = []
    if field_completeness_rate < 0.95:
        issues.append("analysis_fields_incomplete")
    if not freshness_passed:
        issues.append("evidence_out_of_time_window")
    return {
        "quality_passed": len(issues) == 0,
        "quality_issues": issues,
        "field_completeness_rate": field_completeness_rate,
        "evidence_freshness_passed": freshness_passed
    }
