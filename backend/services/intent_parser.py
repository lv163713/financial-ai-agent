import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from core.config import settings


class IntentParserService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            temperature=0.1
        )
        self.prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""
你是 A 股财经查询意图解析器。请将用户问题解析为 JSON，只输出 JSON。

用户问题: {query}

输出字段:
1. raw_query: 原始问题
2. keywords: 关键词数组，最多 5 个
3. sector: 通达信一级行业分类名称（如：金融、采掘、化工、钢铁、有色、电子、家用电器、食品饮料、商业贸易、轻工制造、医药生物、公用事业、交通运输、房地产、有色金属、机械设备、汽车、电子、计算机、传媒、通信、建筑装饰、建筑材料、电力设备、国防军工、美容护理、纺织服饰、社会服务、基础化工、农林牧渔、石油石化、综合、煤炭、非银金融、银行），没有则 null
4. time_range_hours: 整数，时间窗口。如果用户问的是“最近的市场情况”、“最新新闻”、“今天走势”等，设为 24 或 48；如果是普通行业分析或没有明确时间词汇，设为 1440 (即 60 天)
5. intent_type: 仅允许 概览/风险/机会/单主题追踪/重大事件
6. is_realtime_query: 布尔值，如果提到“最新”、“今天”、“实时”、“收盘”等时效性词汇，设为 true
7. prefer_cls: 布尔值，如果用户问“最近发生的大事”、“快讯”、“电报”等，设为 true
"""
        )
        self.chain = self.prompt_template | self.llm

    def parse_intent(self, query: str, market: Optional[str] = None, time_range_hours: int = 24) -> Dict[str, Any]:
        try:
            response = self.chain.invoke({
                "query": query
            })
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            intent = json.loads(text.strip())
            return self._normalize_intent(intent, query)
        except Exception:
            return self._fallback_intent(query)

    def _normalize_intent(
        self,
        intent: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        normalized = {
            "raw_query": query,
            "keywords": self._normalize_keywords(intent.get("keywords"), query),
            "sector": intent.get("sector"),
            "market": "A股",
            "time_range_hours": int(intent.get("time_range_hours", 1440)),
            "intent_type": self._normalize_intent_type(intent.get("intent_type")),
            "is_realtime_query": bool(intent.get("is_realtime_query", False)),
            "prefer_cls": bool(intent.get("prefer_cls", False))
        }
        return normalized

    def _fallback_intent(self, query: str) -> Dict[str, Any]:
        keywords = self._extract_keywords(query)
        is_realtime = self._guess_realtime(query)
        is_major = "大事" in query or "重要事件" in query
        return {
            "raw_query": query,
            "keywords": keywords,
            "sector": self._guess_sector(query),
            "market": "A股",
            "time_range_hours": 24 if is_realtime else 1440,
            "intent_type": "重大事件" if is_major else self._guess_intent_type(query),
            "is_realtime_query": is_realtime,
            "prefer_cls": is_major or "电报" in query or "快讯" in query
        }

    def _normalize_intent_type(self, value: Optional[str]) -> str:
        if value in {"概览", "风险", "机会", "单主题追踪", "重大事件"}:
            return value
        return "概览"

    def _normalize_keywords(self, value: Any, query: str) -> List[str]:
        if isinstance(value, list):
            keywords = [str(item).strip() for item in value if str(item).strip()]
            # 过滤掉过于笼统的词，如 "A股", "影响", "市场" 等
            black_list = {"a股", "影响", "市场", "行业", "板块", "分析", "追踪"}
            keywords = [kw for kw in keywords if kw.lower() not in black_list]
            if keywords:
                return keywords[:5]
        return self._extract_keywords(query)

    def _extract_keywords(self, query: str) -> List[str]:
        separators = ["，", ",", "。", "？", "?", "！", "!", " ", "的", "和"]
        words = [query]
        for sep in separators:
            buffer = []
            for word in words:
                buffer.extend(word.split(sep))
            words = buffer
        keywords = [w.strip() for w in words if len(w.strip()) >= 2]
        return keywords[:5] if keywords else [query[:20]]

    def _guess_sector(self, query: str) -> Optional[str]:
        sector_dict = [
            "金融", "采掘", "化工", "钢铁", "有色", "电子", "家用电器", "食品饮料", "商业贸易", 
            "轻工制造", "医药生物", "公用事业", "交通运输", "房地产", "有色金属", "机械设备", 
            "汽车", "计算机", "传媒", "通信", "建筑装饰", "建筑材料", "电力设备", 
            "国防军工", "美容护理", "纺织服饰", "社会服务", "基础化工", "农林牧渔", "石油石化", 
            "综合", "煤炭", "非银金融", "银行"
        ]
        for sector in sector_dict:
            if sector in query:
                return sector
        return None

    def _guess_intent_type(self, query: str) -> str:
        if "风险" in query or "利空" in query:
            return "风险"
        if "机会" in query or "利好" in query:
            return "机会"
        if "追踪" in query or "跟踪" in query:
            return "单主题追踪"
        return "概览"

    def _guess_realtime(self, query: str) -> bool:
        realtime_keywords = ["最新", "今天", "实时", "收盘", "盘中", "刚出", "新闻", "动态", "最近"]
        for kw in realtime_keywords:
            if kw in query:
                return True
        return False


intent_parser = IntentParserService()
