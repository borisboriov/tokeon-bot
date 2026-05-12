from pathlib import Path

from app.config import settings
from app.providers import make_embeddings, make_llm
from app.store import VectorStore

_SYSTEM_PROMPT = """Ты — помощник службы поддержки платформы Токеон (цифровые финансовые активы, ЦФА).
Отвечай строго на основе предоставленного контекста из базы знаний.
Если ответ не найден в контексте — честно скажи об этом, не придумывай.
Отвечай на том же языке, на котором задан вопрос.
Будь точным и лаконичным."""

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class RAGPipeline:
    def __init__(self) -> None:
        self._embedder = make_embeddings()
        self._llm = make_llm()
        chroma_path = str(_PROJECT_ROOT / settings.chroma_path)
        self._store = VectorStore(chroma_path=chroma_path, provider=settings.embedding_provider)

    def retrieve(self, query: str) -> list[dict]:
        vec = self._embedder.embed_query(query)
        return self._store.query(
            query_vector=vec,
            top_k=settings.top_k,
            score_threshold=settings.retrieval_score_threshold,
        )

    def answer(self, query: str) -> tuple[str, list[dict]]:
        hits = self.retrieve(query)
        if not hits:
            return "Извините, в базе знаний не найдено информации по вашему вопросу.", []

        context_parts = []
        for i, hit in enumerate(hits, 1):
            meta = hit["metadata"]
            source = meta.get("source_file", "")
            title = meta.get("title", "")
            header = f"[{i}] {title} ({source})" if title else f"[{i}] {source}"
            context_parts.append(f"{header}\n{hit['text']}")
        context = "\n\n---\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Контекст из базы знаний:\n\n{context}\n\n"
                    f"Вопрос пользователя: {query}"
                ),
            },
        ]
        reply = self._llm.chat(messages)
        return reply, hits
