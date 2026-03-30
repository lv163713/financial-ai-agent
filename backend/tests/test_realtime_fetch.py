from services.realtime_fetch import RealtimeFetchService


def test_collect_candidate_urls_filters_irrelevant_and_ranks(monkeypatch):
    service = RealtimeFetchService()

    def _fake_search_urls(query):
        return [
            "https://en.wikipedia.org/wiki/Stock_market",
            "https://www.eastmoney.com/news/202603301234.html",
            "https://www.example.com/topic/ai",
            "https://wallstreetcn.com/articles/1234567",
            "https://zhihu.com/question/123"
        ]

    monkeypatch.setattr(service, "_search_urls", _fake_search_urls)
    urls = service._collect_candidate_urls(
        search_queries=["A股 半导体 财经 新闻"],
        exclude_urls={"https://wallstreetcn.com/articles/1234567"}
    )
    assert "https://eastmoney.com/news/202603301234.html" in urls
    assert "https://wallstreetcn.com/articles/1234567" not in urls
    assert all("wikipedia.org" not in url for url in urls)
    assert all("zhihu.com" not in url for url in urls)


def test_normalize_url_filters_and_keeps_key_query_params():
    service = RealtimeFetchService()
    normalized = service._normalize_url("https://www.reuters.com/world/china?id=1001&utm_source=test")
    assert normalized == "https://reuters.com/world/china?id=1001"
    assert service._normalize_url("https://zhihu.com/question/1") == ""
    assert service._normalize_url("https://example.com/search?q=test") == ""


def test_build_search_queries_adds_finance_constraints():
    service = RealtimeFetchService()
    queries = service._build_search_queries(
        intent={"raw_query": "半导体板块风险", "market": "A股", "sector": "半导体"},
        keywords=["半导体", "风险"]
    )
    assert "半导体板块风险 财经 股市" in queries
    assert "A股 半导体 财经 新闻" in queries
