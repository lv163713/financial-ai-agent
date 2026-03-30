from datetime import datetime, timedelta
from services import query_workflow


class _News:
    def __init__(self, news_id: int):
        self.id = news_id
        self.source = "unit-test"
        self.url = f"https://example.com/{news_id}"
        self.title = "测试标题"
        self.created_at = datetime.utcnow()


class _Analysis:
    summary = "测试摘要"
    impact_assessment = "中性"
    affected_sectors = "新能源"
    logical_reasoning = "测试逻辑"


def test_run_query_workflow_trigger_fallback(monkeypatch):
    monkeypatch.setattr(
        query_workflow.intent_parser,
        "parse_intent",
        lambda query, market, time_range_hours: {
            "raw_query": query,
            "keywords": ["测试"],
            "sector": "新能源",
            "market": market,
            "time_range_hours": time_range_hours,
            "intent_type": "概览"
        }
    )
    states = {"count": 0}

    def _fake_search(db, intent):
        states["count"] += 1
        if states["count"] == 1:
            return []
        return [{"news": _News(1), "analysis": _Analysis(), "similarity_score": 0.91}]

    monkeypatch.setattr(query_workflow, "_search_recent_items", _fake_search)
    monkeypatch.setattr(
        query_workflow,
        "_run_fallback_fetch",
        lambda db, intent, matched_items: {
            "attempted": True,
            "search_queries": ["测试"],
            "candidate_urls": ["https://example.com/1"],
            "success_count": 1,
            "failed_count": 0,
            "results": []
        }
    )
    result = query_workflow.run_query_workflow(db=None, query="测试", market="全球", time_range_hours=24)
    assert result["meta"]["fallback_attempted"] is True
    assert result["meta"]["fallback_success_count"] == 1
    assert result["meta"]["retrieved_count"] == 1


def test_validate_output_quality_outdated_evidence():
    intent = {"time_range_hours": 24}
    analysis = {
        "summary": "a",
        "impact_assessment": "中性",
        "affected_sectors": "新能源",
        "logical_reasoning": "b",
        "risk_notice": "c"
    }
    evidence = [
        {
            "source": "x",
            "url": "https://x.com",
            "title": "x",
            "published_at": (datetime.utcnow() - timedelta(hours=50)).isoformat(),
            "similarity_score": 0.7
        }
    ]
    quality = query_workflow._validate_output_quality(intent=intent, analysis=analysis, evidence=evidence)
    assert quality["quality_passed"] is False
    assert "evidence_out_of_time_window" in quality["quality_issues"]
