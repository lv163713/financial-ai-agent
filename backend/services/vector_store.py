import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings
from core.config import settings
from models.rag_document import RagDocument


class VectorStoreService:
    def __init__(self):
        if settings.DASHSCOPE_API_KEY:
            os.environ["DASHSCOPE_API_KEY"] = settings.DASHSCOPE_API_KEY
        self.embedding_client = OpenAIEmbeddings(
            api_key=os.environ.get("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=settings.RAG_EMBEDDING_MODEL
        )

    def upsert_news_document(
        self,
        db: Session,
        news_id: int,
        content: str,
        source: Optional[str],
        market: Optional[str],
        sectors: Optional[str],
        published_at: Optional[datetime]
    ) -> int:
        chunks = self._chunk_text(content)
        if not chunks:
            db.query(RagDocument).filter(RagDocument.news_id == news_id).delete()
            db.commit()
            return 0

        embeddings = self.embedding_client.embed_documents(chunks)
        db.query(RagDocument).filter(RagDocument.news_id == news_id).delete()

        for idx, chunk in enumerate(chunks):
            embedding = embeddings[idx] if idx < len(embeddings) else []
            db.add(
                RagDocument(
                    news_id=news_id,
                    chunk_id=idx,
                    content=chunk,
                    embedding=json.dumps(embedding, ensure_ascii=False),
                    source=source,
                    published_at=published_at,
                    market=market,
                    sectors=sectors
                )
            )
        db.commit()
        return len(chunks)

    def search(
        self,
        db: Session,
        query_text: str,
        market: Optional[str],
        time_range_hours: int,
        top_k: int
    ) -> List[Dict[str, Any]]:
        if not query_text.strip():
            return []

        query_embedding = self.embedding_client.embed_query(query_text)
        start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        rows = (
            db.query(RagDocument)
            .filter(RagDocument.published_at >= start_time)
            .order_by(RagDocument.published_at.desc())
            .limit(settings.RAG_MAX_CANDIDATES)
            .all()
        )
        if market and market != "全球":
            rows = [row for row in rows if row.market in (market, None, "全球")]

        scored: List[Dict[str, Any]] = []
        for row in rows:
            embedding = self._safe_load_embedding(row.embedding)
            if not embedding:
                continue
            similarity = self._cosine_similarity(query_embedding, embedding)
            scored.append(
                {
                    "news_id": row.news_id,
                    "chunk_id": row.chunk_id,
                    "score": round(similarity, 4),
                    "source": row.source,
                    "published_at": row.published_at
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _chunk_text(self, content: str) -> List[str]:
        text = (content or "").strip()
        if not text:
            return []
        size = max(200, settings.RAG_CHUNK_SIZE)
        overlap = min(max(0, settings.RAG_CHUNK_OVERLAP), size // 2)
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + size)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)
        return chunks

    def _safe_load_embedding(self, value: str) -> List[float]:
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [float(item) for item in parsed]
            return []
        except Exception:
            return []

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        length = min(len(a), len(b))
        if length == 0:
            return 0.0
        a_slice = a[:length]
        b_slice = b[:length]
        dot = sum(x * y for x, y in zip(a_slice, b_slice))
        norm_a = sum(x * x for x in a_slice) ** 0.5
        norm_b = sum(y * y for y in b_slice) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


vector_store = VectorStoreService()
