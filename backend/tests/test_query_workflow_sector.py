from services import query_workflow


class _News:
    def __init__(self, news_id: int, title: str, content: str):
        self.id = news_id
        self.source = "unit-test"
        self.url = f"https://example.com/{news_id}"
        self.title = title
        self.content_md = content
        from datetime import datetime
        self.created_at = datetime.utcnow()


class _Ana:
    def __init__(self, sectors: str):
        self.summary = "x"
        self.impact_assessment = "中性"
        self.affected_sectors = sectors
        self.logical_reasoning = "r"


def test_sector_filter_prefers_matched_sector(monkeypatch):
    def _fake_parse_intent(query, market, time_range_hours):
        return {
            "raw_query": query,
            "keywords": ["风险"],
            "sector": "半导体",
            "market": market,
            "time_range_hours": time_range_hours,
            "intent_type": "风险"
        }

    def _fake_search(db, intent):
        a = {"news": _News(1, "生猪价格波动", "生猪出栏"), "analysis": _Ana("猪肉"), "similarity_score": 0.95}
        b = {"news": _News(2, "半导体景气回落风险", "半导体库存周期"), "analysis": _Ana("半导体"), "similarity_score": 0.8}
        return [a, b]

    def _fake_fallback(db, intent, matched_items):
        return {"attempted": False, "search_queries": [], "candidate_urls": [], "success_count": 0, "failed_count": 0, "results": []}

    monkeypatch.setattr(query_workflow.intent_parser, "parse_intent", _fake_parse_intent)
    monkeypatch.setattr(query_workflow, "_search_recent_items", _fake_search)
    monkeypatch.setattr(query_workflow, "_run_fallback_fetch", _fake_fallback)

    res = query_workflow.run_query_workflow(db=None, query="A股半导体板块有哪些风险？", market="A股", time_range_hours=24)
    assert res["analysis"]["affected_sectors"].find("半导体") != -1
    assert all("猪肉" not in ev["title"] for ev in res["evidence"])
