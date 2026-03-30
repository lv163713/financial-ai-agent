from typing import Dict, Any, List, Set
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import re
import requests
from sqlalchemy.orm import Session
from core.config import settings
from services.pipeline import run_batch_ingest_pipeline


class RealtimeFetchService:
    FINANCE_DOMAIN_HINTS = {
        "eastmoney.com", "10jqka.com.cn", "stcn.com", "cs.com.cn", "cnstock.com", "yicai.com",
        "cls.cn", "wallstreetcn.com", "caixin.com", "jrj.com.cn", "finance.sina.com.cn",
        "finance.qq.com", "finance.ifeng.com", "reuters.com", "bloomberg.com", "cnbc.com",
        "marketwatch.com", "investing.com", "seekingalpha.com", "ft.com"
    }
    BLOCKED_DOMAINS = {
        "wikipedia.org", "zhihu.com", "bilibili.com", "douban.com", "baike.baidu.com",
        "tieba.baidu.com", "sohu.com"
    }
    FINANCE_TERMS = {
        "finance", "stock", "market", "equity", "bond", "futures", "index", "earnings",
        "ipo", "economy", "macro", "fund", "财经", "金融", "股市", "a股", "美股", "港股",
        "指数", "期货", "债券", "基金", "宏观", "财报", "快讯"
    }
    BLOCKED_PATH_TERMS = {
        "/tag", "/topic", "/search", "/video", "/live", "/course", "/docs", "/help", "/about",
        "/account", "/login", "/signup", "/user", "/community", "/forum"
    }
    QUERY_ALLOW_KEYS = {"id", "docid", "article", "newsid", "p", "v"}

    def trigger_fallback(self, db: Session, intent: Dict[str, Any], exclude_urls: Set[str], force_sector_filter: bool = False) -> Dict[str, Any]:
        keywords = intent.get("keywords", [])[:5]
        search_queries = self._build_search_queries(intent=intent, keywords=keywords)
        candidate_urls = self._collect_candidate_urls(search_queries=search_queries, exclude_urls=exclude_urls)
        if not candidate_urls:
            return {
                "attempted": True,
                "search_queries": search_queries,
                "candidate_urls": [],
                "success_count": 0,
                "failed_count": 0,
                "results": []
            }
        
        # 增加行业硬过滤逻辑
        target_sector = intent.get("sector")
        payload_items = []
        for url in candidate_urls:
            payload_items.append({
                "url": url, 
                "source": None,
                "required_sector": target_sector if force_sector_filter else None
            })

        ingest_result = run_batch_ingest_pipeline(
            db=db,
            items=payload_items,
            max_concurrency=min(3, len(payload_items)),
            retry_times=1
        )
        return {
            "attempted": True,
            "search_queries": search_queries,
            "candidate_urls": candidate_urls,
            "success_count": ingest_result.get("success_count", 0),
            "failed_count": ingest_result.get("failed_count", 0),
            "results": ingest_result.get("results", [])
        }

    def _build_search_queries(self, intent: Dict[str, Any], keywords: List[str]) -> List[str]:
        base_query = (intent.get("raw_query") or "").strip()
        market = (intent.get("market") or "").strip()
        sector = (intent.get("sector") or "").strip()
        query_set: List[str] = []
        if base_query:
            query_set.append(base_query)
        if sector and market:
            query_set.append(f"{market} {sector} 财经 新闻")
        elif sector:
            query_set.append(f"{sector} 财经 新闻")
        elif market:
            query_set.append(f"{market} 财经 新闻")
        if base_query:
            query_set.append(f"{base_query} 财经 股市")
        if keywords:
            query_set.append(f"{' '.join(keywords)} 财经 资讯")
            query_set.append(" ".join(keywords))
        
        # 财联社电报优化
        if intent.get("prefer_cls"):
            query_set.insert(0, f"财联社电报 {base_query}")
            query_set.insert(1, f"财联社 实时 快讯 {sector or ''}")
            
        compacted: List[str] = []
        existed = set()
        for query in query_set:
            clean = " ".join(query.split())
            if not clean or clean in existed:
                continue
            compacted.append(clean)
            existed.add(clean)
        return compacted[: settings.RAG_FALLBACK_MAX_QUERIES]

    def _collect_candidate_urls(self, search_queries: List[str], exclude_urls: Set[str]) -> List[str]:
        excluded_normalized = {self._normalize_url(url) for url in exclude_urls}
        scored_map: Dict[str, float] = {}
        for query in search_queries:
            query_terms = self._extract_query_terms(query)
            for url in self._search_urls(query):
                normalized = self._normalize_url(url)
                if not normalized or normalized in excluded_normalized:
                    continue
                score = self._score_url_relevance(normalized, query_terms)
                if score < 0.35:
                    continue
                current = scored_map.get(normalized)
                if current is None or score > current:
                    scored_map[normalized] = score
        ranked = sorted(scored_map.items(), key=lambda item: item[1], reverse=True)
        return [url for url, _ in ranked[: settings.RAG_FALLBACK_MAX_URLS]]

    def _search_urls(self, query: str) -> List[str]:
        endpoint = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        try:
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=settings.RAG_FALLBACK_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except Exception:
            return []
        html = response.text
        raw_links = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"', html)
        if not raw_links:
            raw_links = re.findall(r'href="([^"]+)"', html)
        urls: List[str] = []
        collect_limit = max(settings.RAG_FALLBACK_MAX_URLS * 4, settings.RAG_FALLBACK_MAX_URLS)
        for link in raw_links:
            real_url = self._extract_real_url(link)
            if not real_url:
                continue
            if real_url not in urls:
                urls.append(real_url)
            if len(urls) >= collect_limit:
                break
        return urls

    def _extract_real_url(self, link: str) -> str:
        decoded = unquote(link).strip()
        if decoded.startswith("//"):
            decoded = f"https:{decoded}"
        if "duckduckgo.com/l/?" in decoded:
            parsed = urlparse(decoded)
            params = parse_qs(parsed.query)
            target = params.get("uddg", [])
            if target:
                decoded = unquote(target[0])
        parsed = urlparse(decoded)
        if parsed.scheme not in {"http", "https"}:
            return ""
        host = parsed.netloc.lower()
        if "duckduckgo.com" in host:
            return ""
        return decoded

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ""
        host = parsed.netloc.lower().strip()
        if host.startswith("www."):
            host = host[4:]
        if self._is_blocked_domain(host):
            return ""
        path = (parsed.path or "").rstrip("/")
        if path and self._is_blocked_path(path.lower()):
            return ""
        if not path and not parsed.query:
            return ""
        if re.search(r"\.(jpg|jpeg|png|gif|svg|webp|pdf|zip|rar|mp4|mp3)$", path, flags=re.IGNORECASE):
            return ""
        query = self._filter_query(parsed.query)
        normalized = f"{parsed.scheme}://{host}{path}"
        if query:
            normalized = f"{normalized}?{query}"
        return normalized

    def _extract_query_terms(self, query: str) -> List[str]:
        terms = [part.strip().lower() for part in re.split(r"[\s,，。;；|/]+", query) if part.strip()]
        return [term for term in terms if len(term) >= 2][:8]

    def _is_blocked_domain(self, host: str) -> bool:
        for blocked in self.BLOCKED_DOMAINS:
            if host == blocked or host.endswith(f".{blocked}"):
                return True
        return False

    def _is_blocked_path(self, path: str) -> bool:
        return any(path.startswith(item) for item in self.BLOCKED_PATH_TERMS)

    def _filter_query(self, query: str) -> str:
        if not query:
            return ""
        params = parse_qs(query, keep_blank_values=False)
        compact: List[str] = []
        for key in sorted(params.keys()):
            key_lc = key.lower()
            if key_lc not in self.QUERY_ALLOW_KEYS:
                continue
            value = params[key][0].strip() if params[key] else ""
            if value:
                compact.append(f"{key_lc}={value}")
        return "&".join(compact)

    def _score_url_relevance(self, url: str, query_terms: List[str]) -> float:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path_query = f"{parsed.path} {parsed.query}".lower()
        score = 0.0
        for trusted in self.FINANCE_DOMAIN_HINTS:
            if host == trusted or host.endswith(f".{trusted}"):
                score += 0.7
                break
        if score < 0.7 and any(token in host for token in ["finance", "stock", "market", "fund", "jrj", "caijing"]):
            score += 0.3
        if any(term in path_query for term in self.FINANCE_TERMS):
            score += 0.2
        keyword_hits = sum(1 for term in query_terms if term in path_query)
        score += min(0.3, keyword_hits * 0.1)
        if any(term in path_query for term in ["/news", "/article", "/kuaixun", "/express", "/flash"]):
            score += 0.1
        if any(token in path_query for token in ["/video", "/live", "/topic", "/tag", "/search"]):
            score -= 0.25
        return round(score, 4)


realtime_fetch_service = RealtimeFetchService()
