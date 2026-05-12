"""Run a category-appropriate chunker on KB files and print samples.

Usage:
    python scripts/preview_chunks.py                              # representative sample across categories
    python scripts/preview_chunks.py --category instructions      # 3 files from one category
    python scripts/preview_chunks.py --category law --all         # every file in category
    python scripts/preview_chunks.py --category law --files law_fz259.txt
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunkers import chunk_by_category  # noqa: E402

DEFAULT_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
CATEGORIES = ["instructions", "law", "book", "business_requirements"]
DEFAULT_SAMPLE: list[tuple[str, str]] = [
    ("instructions", "often.questions.txt"),
    ("law", "law_fz259.txt"),
    ("book", "about_cfa.txt"),
    ("business_requirements", "defolt.emitenta.txt"),
]


def preview(path: Path, category: str, max_chunks: int) -> None:
    chunks = chunk_by_category(path, category)
    fmt = chunks[0].metadata["format"] if chunks else "(empty)"
    sizes = [len(c.text) for c in chunks]
    print(f"\n=== [{category}] {path.name}  ({len(chunks)} chunks, layout={fmt}) ===")
    if sizes:
        print(f"    sizes: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes) // len(sizes)}, total={sum(sizes)}")
    for chunk in chunks[:max_chunks]:
        head = chunk.text[:220].replace("\n", " | ")
        more = "..." if len(chunk.text) > 220 else ""
        print(f"\n  [#{chunk.metadata['chunk_index']}] {chunk.metadata['title']}")
        print(f"      breadcrumbs: {' > '.join(chunk.metadata['breadcrumbs'])}")
        print(f"      size: {len(chunk.text)} chars")
        print(f"      text: {head}{more}")
    if len(chunks) > max_chunks:
        print(f"\n  ... ({len(chunks) - max_chunks} more chunks)")


def _category_root(kb: Path, category: str) -> Path:
    return kb / category


def _resolve(kb: Path, category: str, fname: str) -> Path | None:
    root = _category_root(kb, category)
    direct = root / fname
    if direct.exists():
        return direct
    matches = list(root.rglob(fname))
    return matches[0] if matches else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", type=Path, default=DEFAULT_KB_PATH)
    ap.add_argument("--category", choices=CATEGORIES, default=None,
                    help="Category to preview (default: cross-category sample)")
    ap.add_argument("--files", nargs="*", default=None,
                    help="Specific filenames inside --category to preview")
    ap.add_argument("--all", action="store_true",
                    help="Preview every .txt in --category (recursive)")
    ap.add_argument("--max", type=int, default=3, help="Chunks shown per file")
    args = ap.parse_args()

    if args.category is None:
        for cat, fname in DEFAULT_SAMPLE:
            path = _resolve(args.kb, cat, fname)
            if path is None:
                print(f"MISSING: [{cat}] {fname}", file=sys.stderr)
                continue
            preview(path, cat, args.max)
        return 0

    cat_root = _category_root(args.kb, args.category)
    if args.all:
        targets = sorted(cat_root.rglob("*.txt"))
    elif args.files:
        targets = []
        for fname in args.files:
            resolved = _resolve(args.kb, args.category, fname)
            if resolved is None:
                print(f"MISSING: [{args.category}] {fname}", file=sys.stderr)
                continue
            targets.append(resolved)
    else:
        targets = sorted(cat_root.rglob("*.txt"))[:3]

    for path in targets:
        preview(path, args.category, args.max)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
