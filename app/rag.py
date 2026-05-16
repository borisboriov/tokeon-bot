import csv
import datetime
from pathlib import Path

from app.config import settings
from app.filters import filter_input, filter_output
from app.prompts import dominant_category, get_prompt
from app.providers import make_embeddings, make_llm
from app.store import VectorStore

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_PATH = _PROJECT_ROOT / "logs" / "requests.csv"


def _log(query: str, answer: str, sources: list[dict], filtered: bool) -> None:
    _LOG_PATH.parent.mkdir(exist_ok=True)
    is_new = not _LOG_PATH.exists()
    with _LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["timestamp", "query", "answer", "sources", "filtered"])
        source_titles = " | ".join(
            s["metadata"].get("source_file", "") for s in sources
        )
        writer.writerow([
            datetime.datetime.now().isoformat(timespec="seconds"),
            query,
            answer[:300],
            source_titles,
            filtered,
        ])

_FALLBACK = (
    "К сожалению, я не нашёл подходящей информации в базе знаний платформы Токеон. "
    "Пожалуйста, обратитесь в службу поддержки."
)

_MAX_HISTORY = 5  # pairs to include in prompt

# Jargon → canonical terms expansion for retrieval.
_JARGON_MAP = {
    "бумаги": "ЦФА цифровые финансовые активы",
    "бумага": "ЦФА цифровой финансовый актив",
    "активы": "ЦФА цифровые финансовые активы",
    "инструменты": "ЦФА цифровые финансовые активы",
    "зарегать": "зарегистрироваться регистрация",
    "зарегиться": "зарегистрироваться регистрация",
    "аккаунт": "личный кабинет учётная запись",
    "бабки": "денежные средства деньги",
    "вывести": "вывод денежных средств кошелёк",
    "купить": "купить ЦФА приобрести",
    "продать": "продать ЦФА реализовать",
    "цыфровые": "цифровые",
    "цыфровой": "цифровой",
}


def _expand_query(query: str) -> str:
    lower = query.lower()
    extras = [exp for jargon, exp in _JARGON_MAP.items() if jargon in lower]
    return f"{query} {' '.join(extras)}".strip() if extras else query


class RAGPipeline:
    def __init__(self) -> None:
        self._embedder = make_embeddings()
        self._llm = make_llm()
        chroma_path = str(_PROJECT_ROOT / settings.chroma_path)
        self._store = VectorStore(chroma_path=chroma_path, provider=settings.embedding_provider)

    def retrieve(self, query: str) -> list[dict]:
        vec = self._embedder.embed_query(_expand_query(query))
        return self._store.query(
            query_vector=vec,
            top_k=settings.top_k,
            score_threshold=settings.retrieval_score_threshold,
        )

    def answer(
        self,
        query: str,
        history: list[tuple[str, str]] | None = None,
    ) -> tuple[str, list[dict]]:
        # --- input filter ---
        cleaned_query, refusal = filter_input(query)
        if refusal:
            _log(query, refusal, [], filtered=True)
            return refusal, []

        # --- retrieval ---
        hits = self.retrieve(cleaned_query)
        if not hits:
            _log(query, _FALLBACK, [], filtered=False)
            return _FALLBACK, []

        # --- build context ---
        context_parts = []
        for i, hit in enumerate(hits, 1):
            meta = hit["metadata"]
            source = meta.get("source_file", "")
            title = meta.get("title", "")
            header = f"[{i}] {title} ({source})" if title else f"[{i}] {source}"
            context_parts.append(f"{header}\n{hit['text']}")
        context = "\n\n---\n\n".join(context_parts)

        # --- prompt routing ---
        category = dominant_category(hits)
        system_prompt = get_prompt(category)

        # --- build messages with history ---
        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        if history:
            for user_msg, assistant_msg in history[-_MAX_HISTORY:]:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": assistant_msg})

        messages.append({
            "role": "user",
            "content": (
                f"Контекст из базы знаний:\n\n{context}\n\n"
                f"Вопрос пользователя: {cleaned_query}"
            ),
        })

        # --- generate ---
        reply = self._llm.chat(messages)

        # --- output filter ---
        reply = filter_output(reply)

        _log(query, reply, hits, filtered=False)
        return reply, hits
