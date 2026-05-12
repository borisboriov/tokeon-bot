"""Inspect the Tokeon knowledge base: walk YAML manifests from root.yaml,
list all referenced .txt files, print per-category stats.

Usage:
    python scripts/inspect_kb.py
    python scripts/inspect_kb.py --kb path/to/knowledge_base
"""
import argparse
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"


@dataclass(frozen=True)
class KBFile:
    path: Path        # absolute path on disk
    rel_path: Path    # relative to KB root
    category: str     # top-level dir under KB root
    yaml_key: str
    manifest: Path    # which YAML referenced this file


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_kb(root_yaml: Path) -> tuple[list[KBFile], Path]:
    root_yaml = root_yaml.resolve()
    kb_root = root_yaml.parent
    files: list[KBFile] = []

    def visit(manifest: Path) -> None:
        data = _load_yaml(manifest)
        for imp in data.get("imports") or []:
            visit((manifest.parent / imp).resolve())
        for key, entry in (data.get("docs") or {}).items():
            source = entry.get("source")
            if not source:
                continue
            src = (manifest.parent / source).resolve()
            try:
                rel = src.relative_to(kb_root)
            except ValueError:
                rel = Path(src.name)
            category = rel.parts[0] if rel.parts else "?"
            files.append(KBFile(src, rel, category, key, manifest))

    visit(root_yaml)
    return files, kb_root


def _fmt_size(n: int) -> str:
    f = float(n)
    for unit in ("B", "KB", "MB"):
        if f < 1024 or unit == "MB":
            return f"{int(f)} {unit}" if unit == "B" else f"{f:.1f} {unit}"
        f /= 1024
    return f"{int(n)} B"


def report(files: list[KBFile], kb_root: Path) -> None:
    by_cat: dict[str, list[KBFile]] = defaultdict(list)
    for kb in files:
        by_cat[kb.category].append(kb)

    print(f"KB root: {kb_root}")
    print(f"Files referenced in YAML: {len(files)}\n")

    header = f"{'category':<22}{'count':>7}{'total':>12}{'avg':>12}{'min':>11}{'max':>11}"
    print(header)
    print("-" * len(header))

    grand = 0
    for cat in sorted(by_cat):
        sizes = [kb.path.stat().st_size for kb in by_cat[cat] if kb.path.exists()]
        total = sum(sizes)
        grand += total
        avg = int(statistics.mean(sizes)) if sizes else 0
        smin = min(sizes) if sizes else 0
        smax = max(sizes) if sizes else 0
        print(f"{cat:<22}{len(by_cat[cat]):>7}"
              f"{_fmt_size(total):>12}{_fmt_size(avg):>12}"
              f"{_fmt_size(smin):>11}{_fmt_size(smax):>11}")
    print("-" * len(header))
    print(f"{'TOTAL':<22}{len(files):>7}{_fmt_size(grand):>12}\n")

    for cat in sorted(by_cat):
        print(f"[{cat}] {len(by_cat[cat])} files")
        for kb in sorted(by_cat[cat], key=lambda x: x.rel_path):
            size = kb.path.stat().st_size if kb.path.exists() else 0
            marker = "" if kb.path.exists() else "   (MISSING)"
            print(f"  {str(kb.rel_path):<62}{_fmt_size(size):>10}{marker}")
        print()

    referenced = {kb.path for kb in files}
    on_disk = {p.resolve() for p in kb_root.rglob("*.txt")}
    orphans = on_disk - referenced
    if orphans:
        print(f"WARNING: {len(orphans)} .txt files on disk but NOT referenced in YAML:")
        for p in sorted(orphans):
            try:
                print(f"  {p.relative_to(kb_root)}")
            except ValueError:
                print(f"  {p}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect the Tokeon knowledge base")
    ap.add_argument("--kb", type=Path, default=DEFAULT_KB_PATH,
                    help=f"KB root containing root.yaml (default: {DEFAULT_KB_PATH})")
    args = ap.parse_args()

    root_yaml = args.kb / "root.yaml"
    if not root_yaml.exists():
        print(f"root.yaml not found at {root_yaml}", file=sys.stderr)
        return 1

    files, kb_root = parse_kb(root_yaml)
    report(files, kb_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
