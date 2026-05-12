"""Run FAQChunker on instructions/ files, print samples for eyeballing.

Usage:
    python scripts/preview_chunks.py                       # representative sample
    python scripts/preview_chunks.py --files often.questions.txt
    python scripts/preview_chunks.py --all                 # every file in instructions/
"""
import argparse
import sys
from pathlib import Path

# Make app/ importable when running scripts from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunkers import FAQChunker  # noqa: E402

DEFAULT_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
DEFAULT_SAMPLE = [
    "often.questions.txt",
    "terminology.txt",
    "wallet.txt",
    "registration.fiz.txt",
    "cryptographic_keys.txt",
]


def preview(path: Path, max_chunks: int) -> None:
    chunker = FAQChunker(category="instructions")
    chunks = chunker.chunk_file(path)
    fmt = chunks[0].metadata["format"] if chunks else "(empty)"
    print(f"\n=== {path.name}  ({len(chunks)} chunks, layout={fmt}) ===")
    for chunk in chunks[:max_chunks]:
        head = chunk.text[:220].replace("\n", "  | ")
        more = "..." if len(chunk.text) > 220 else ""
        print(f"\n  [#{chunk.metadata['chunk_index']}] {chunk.metadata['title']}")
        print(f"      breadcrumbs: {' > '.join(chunk.metadata['breadcrumbs'])}")
        print(f"      size: {len(chunk.text)} chars")
        print(f"      text: {head}{more}")
    if len(chunks) > max_chunks:
        print(f"\n  ... ({len(chunks) - max_chunks} more chunks)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", type=Path, default=DEFAULT_KB_PATH,
                    help=f"KB root (default: {DEFAULT_KB_PATH})")
    ap.add_argument("--files", nargs="*", default=None,
                    help="Specific filenames inside instructions/ to preview")
    ap.add_argument("--all", action="store_true",
                    help="Preview every .txt file in instructions/")
    ap.add_argument("--max", type=int, default=3,
                    help="Chunks to show per file (default: 3)")
    args = ap.parse_args()

    instructions_dir = args.kb / "instructions"
    if args.all:
        targets = sorted(instructions_dir.glob("*.txt"))
    elif args.files:
        targets = [instructions_dir / f for f in args.files]
    else:
        targets = [instructions_dir / f for f in DEFAULT_SAMPLE]

    for path in targets:
        if not path.exists():
            print(f"MISSING: {path}", file=sys.stderr)
            continue
        preview(path, max_chunks=args.max)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
