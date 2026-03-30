import re
import html
import json
import requests
from typing import Optional
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from core.logger import get_logger

logger = get_logger("services.scraper")

class JinaReaderService:
    """
    使用 Jina Reader API 进行智能网页抓取。
    内置了针对财联社和华尔街见闻的优化解析逻辑，以提高抓取速度和稳定性。
    """
    
    BASE_URL = "https://r.jina.ai/"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            
    def fetch_markdown(self, target_url: str) -> Optional[str]:
        # 针对特定来源进行优化抓取
        if "cls.cn/telegraph" in target_url:
            res = self._fetch_cailianshe(target_url)
            if res: return res
            
        if "wallstreetcn.com" in target_url:
            res = self._fetch_wallstreetcn(target_url)
            if res: return res

        request_url = f"{self.BASE_URL}{target_url}"

        try:
            response = requests.get(request_url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                return response.text
            logger.warning(f"jina_reader_status_error status={response.status_code}")
            return self._fetch_direct_markdown(target_url)
        except requests.exceptions.RequestException as e:
            logger.warning(f"jina_reader_request_error url={target_url} error={str(e)}")
            return self._fetch_direct_markdown(target_url)

    def _fetch_cailianshe(self, target_url: str) -> Optional[str]:
        """专门针对财联社电报的优化抓取，直接从页面提取 Next.js 初始状态"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        disable_warnings(InsecureRequestWarning)
        try:
            response = requests.get(target_url, headers=headers, timeout=20, verify=False)
            if response.status_code != 200:
                return None
            
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text)
            if m:
                data = json.loads(m.group(1))
                telegraphs = data.get('props', {}).get('initialState', {}).get('telegraph', {}).get('telegraphList', [])
                if not telegraphs:
                    return None
                
                content_list = []
                for item in telegraphs[:50]:
                    title = item.get('title', '')
                    content = item.get('content', '')
                    text = f"【{title}】\n{content}" if title else content
                    content_list.append(text)
                
                return f"Title: 财联社电报\nURL Source: {target_url}\n\n" + "\n\n---\n\n".join(content_list)
        except Exception as e:
            logger.error(f"fetch_cailianshe_error url={target_url} error={str(e)}")
        return None

    def _fetch_wallstreetcn(self, target_url: str) -> Optional[str]:
        """专门针对华尔街见闻的优化抓取，直接调用其后端 API 获取数据"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        disable_warnings(InsecureRequestWarning)
        try:
            if "flash" in target_url or "live" in target_url:
                api_url = "https://api.wallstreetcn.com/apiv1/content/lives?channel=global-channel&limit=30"
                title_prefix = "华尔街见闻实时快讯"
            else:
                api_url = "https://api.wallstreetcn.com/apiv1/content/articles?channel=global&limit=30"
                title_prefix = "华尔街见闻全球资讯"
                
            response = requests.get(api_url, headers=headers, timeout=20, verify=False)
            if response.status_code != 200:
                return None
                
            data = response.json()
            items = data.get('data', {}).get('items', [])
            if not items:
                return None
                
            content_list = []
            for item in items:
                title = item.get('title', '')
                # 快讯的正文在 content_text 中，文章在 content_short 或 content 中
                content = item.get('content_text') or item.get('content_short') or item.get('content', '')
                content = re.sub(r'<[^>]+>', '', content) # 简单清理 HTML 标签
                
                text = f"【{title}】\n{content}" if title else content
                if text.strip():
                    content_list.append(text.strip())
            
            return f"Title: {title_prefix}\nURL Source: {target_url}\n\n" + "\n\n---\n\n".join(content_list)
        except Exception as e:
            logger.error(f"fetch_wallstreetcn_error url={target_url} error={str(e)}")
        return None

    def _fetch_direct_markdown(self, target_url: str) -> Optional[str]:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        disable_warnings(InsecureRequestWarning)
        try:
            response = requests.get(target_url, headers=headers, timeout=20)
        except requests.exceptions.SSLError:
            try:
                response = requests.get(target_url, headers=headers, timeout=20, verify=False)
            except requests.exceptions.RequestException as e:
                logger.warning(f"direct_fetch_request_error url={target_url} error={str(e)}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"direct_fetch_request_error url={target_url} error={str(e)}")
            return None
        try:
            if response.status_code != 200:
                logger.warning(f"direct_fetch_status_error status={response.status_code} url={target_url}")
                return None
            page_text = response.text or ""
            title = self._extract_title(page_text, target_url)
            markdown = self._html_to_markdown(page_text)
            if not markdown:
                return None
            return f"Title: {title}\n\n{markdown}"
        except Exception:
            return None

    def _extract_title(self, page_text: str, fallback_title: str) -> str:
        matched = re.search(r"<title[^>]*>(.*?)</title>", page_text, flags=re.IGNORECASE | re.DOTALL)
        if not matched:
            return fallback_title[:255]
        title = html.unescape(matched.group(1))
        title = re.sub(r"\s+", " ", title).strip()
        return (title or fallback_title)[:255]

    def _html_to_markdown(self, page_text: str) -> str:
        content = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", page_text)
        content = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", content)
        content = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", content)
        content = re.sub(r"(?is)<br\s*/?>", "\n", content)
        content = re.sub(r"(?is)</p\s*>", "\n\n", content)
        content = re.sub(r"(?is)</(h1|h2|h3|h4|h5|h6|li|div|section|article)\s*>", "\n", content)
        content = re.sub(r"(?is)<[^>]+>", " ", content)
        content = html.unescape(content)
        lines = [re.sub(r"\s+", " ", line).strip() for line in content.splitlines()]
        lines = [line for line in lines if len(line) >= 20]
        return "\n".join(lines[:300])

# 单例模式，方便在其他地方直接导入使用
jina_reader = JinaReaderService()
