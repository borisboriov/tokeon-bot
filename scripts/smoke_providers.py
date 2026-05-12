"""Quick sanity check: LLM responds, local embeddings produce vectors."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers import make_embeddings, make_llm


def main() -> None:
    print("=== LLM smoke test ===")
    llm = make_llm()
    reply = llm.ask("Привет! Ответь одним словом: всё работает?")
    print(f"LLM reply: {reply!r}\n")

    print("=== Embeddings smoke test ===")
    emb = make_embeddings()
    vecs = emb.embed_documents(["Что такое ЦФА?", "Как открыть счёт на платформе Токеон?"])
    print(f"Vectors: {len(vecs)} × {len(vecs[0])} dims")

    q = emb.embed_query("открыть счёт")
    print(f"Query vector: {len(q)} dims")
    print(f"First 5 values: {[round(x, 4) for x in q[:5]]}")
    print("\nAll good.")


if __name__ == "__main__":
    main()
