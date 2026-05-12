"""Quick end-to-end RAG check: a few representative questions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag import RAGPipeline

QUESTIONS = [
    "Что такое ЦФА?",
    "Как зарегистрироваться на платформе Токеон?",
    "Какие документы нужны для открытия счёта физическому лицу?",
]


def main() -> None:
    rag = RAGPipeline()
    for q in QUESTIONS:
        print(f"\n{'='*70}")
        print(f"Вопрос: {q}")
        print("-" * 70)
        answer, hits = rag.answer(q)
        print(f"Ответ:\n{answer}")
        print(f"\nИсточники ({len(hits)}):")
        for h in hits:
            m = h["metadata"]
            print(f"  [{h['score']:.3f}] {m.get('source_file')} — {m.get('title', '')[:60]}")


if __name__ == "__main__":
    main()
