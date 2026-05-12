"""Ingest all KB files into ChromaDB.

Usage:
    python scripts/ingest.py              # full ingest (resets existing collection)
    python scripts/ingest.py --dry-run    # chunk only, skip embed + store
    python scripts/ingest.py --batch-size 32
"""
import argparse
import sys
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from inspect_kb import parse_kb  # noqa: E402

from app.chunkers import chunk_by_category  # noqa: E402
from app.config import settings  # noqa: E402
from app.providers import make_embeddings  # noqa: E402
from app.store import VectorStore  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest KB into ChromaDB")
    ap.add_argument("--dry-run", action="store_true", help="chunk only, no embed/store")
    ap.add_argument("--batch-size", type=int, default=64, metavar="N")
    args = ap.parse_args()

    kb_root_path = Path(settings.kb_path)
    if not kb_root_path.is_absolute():
        kb_root_path = _PROJECT_ROOT / kb_root_path
    root_yaml = kb_root_path / "root.yaml"

    if not root_yaml.exists():
        print(f"ERROR: root.yaml not found at {root_yaml}", file=sys.stderr)
        return 1

    kb_files, kb_root = parse_kb(root_yaml)
    print(f"KB root : {kb_root}")
    print(f"Files   : {len(kb_files)}\n")

    # --- chunk all files ---
    all_chunks = []
    for kb in sorted(kb_files, key=lambda x: x.rel_path):
        chunks = chunk_by_category(kb.path, kb.category)
        all_chunks.extend(chunks)
        print(f"  {str(kb.rel_path):<65} {len(chunks):>4} chunks")

    print(f"\nTotal chunks : {len(all_chunks)}")

    if args.dry_run:
        print("Dry run — skipping embed + store.")
        return 0

    # --- embed in batches ---
    embedder = make_embeddings()
    print(f"\nEmbedding ({settings.embedding_provider}) ...")
    t0 = time.time()
    texts = [c.text for c in all_chunks]
    vectors: list[list[float]] = []
    bs = args.batch_size
    for i in range(0, len(texts), bs):
        batch = texts[i : i + bs]
        vectors.extend(embedder.embed_documents(batch))
        done = min(i + bs, len(texts))
        print(f"  {done}/{len(texts)}", end="\r")
    elapsed = time.time() - t0
    print(f"  {len(texts)}/{len(texts)} vectors  ({elapsed:.1f}s)      ")

    # --- store ---
    chroma_path = str(_PROJECT_ROOT / settings.chroma_path)
    store = VectorStore(chroma_path=chroma_path, provider=settings.embedding_provider)
    store.reset()
    store.add_chunks(all_chunks, vectors)
    print(f"\nCollection : '{store.name}'")
    print(f"Vectors    : {store.count()}")
    print(f"Chroma dir : {chroma_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
