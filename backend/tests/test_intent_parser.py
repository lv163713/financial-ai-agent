from services.intent_parser import intent_parser


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeChain:
    def invoke(self, payload):
        return _FakeResponse(
            """
```json
{
  "raw_query": "忽略",
  "keywords": ["新能源", "利空"],
  "sector": "新能源",
  "market": "无效市场",
  "time_range_hours": 999,
  "intent_type": "未知"
}
```
"""
        )


def test_parse_intent_normalize(monkeypatch):
    monkeypatch.setattr(intent_parser, "chain", _FakeChain())
    result = intent_parser.parse_intent(query="最近新能源有利空吗", market="A股", time_range_hours=24)
    assert result["raw_query"] == "最近新能源有利空吗"
    assert result["market"] == "A股"
    assert result["time_range_hours"] == 48
    assert result["intent_type"] == "概览"
    assert result["keywords"][:2] == ["新能源", "利空"]
