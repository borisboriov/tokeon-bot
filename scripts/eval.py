"""Run eval questions through the RAG pipeline and print/save results.

Usage:
    python scripts/eval.py                      # all questions
    python scripts/eval.py --group colloquial   # one group only
    python scripts/eval.py --save               # also write data/eval_results.txt
"""
import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.rag import RAGPipeline  # noqa: E402

_QUESTIONS_FILE = _PROJECT_ROOT / "data" / "eval_questions.json"
_RESULTS_FILE = _PROJECT_ROOT / "data" / "eval_results.txt"

_GROUP_LABELS = {
    "kb_vs_internet": "КБ vs интернет",
    "colloquial": "Жаргон / разговорная речь",
    "edge_cases": "Граничные случаи",
}


def run(questions: list[dict], rag: RAGPipeline, save: bool) -> None:
    lines: list[str] = []

    current_group = None
    for q in questions:
        group = q["group"]
        if group != current_group:
            header = f"\n{'='*70}\n  {_GROUP_LABELS.get(group, group)}\n{'='*70}"
            print(header)
            lines.append(header)
            current_group = group

        separator = f"\n[{q['id']}] {q['question']}"
        note_line = f"  ↳ {q['note']}"
        print(separator)
        print(note_line)
        lines.extend([separator, note_line])

        answer, hits = rag.answer(q["question"])

        answer_block = f"\nОТВЕТ:\n{answer}"
        print(answer_block)
        lines.append(answer_block)

        if hits:
            src_header = "\nИСТОЧНИКИ:"
            print(src_header)
            lines.append(src_header)
            for h in hits:
                m = h["metadata"]
                src_line = (
                    f"  [{h['score']:.3f}] {m.get('source_file')} — "
                    f"{m.get('title', '')[:55]}"
                )
                print(src_line)
                lines.append(src_line)
        else:
            no_src = "  (источники не найдены)"
            print(no_src)
            lines.append(no_src)

        divider = "-" * 70
        print(divider)
        lines.append(divider)

    if save:
        _RESULTS_FILE.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nРезультаты сохранены: {_RESULTS_FILE}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate RAG on golden question set")
    ap.add_argument("--group", help="filter by group name")
    ap.add_argument("--save", action="store_true", help=f"save results to {_RESULTS_FILE}")
    args = ap.parse_args()

    questions: list[dict] = json.loads(_QUESTIONS_FILE.read_text(encoding="utf-8"))
    if args.group:
        questions = [q for q in questions if q["group"] == args.group]
        if not questions:
            print(f"No questions for group {args.group!r}", file=sys.stderr)
            return 1

    print("Загружаю RAG pipeline ...")
    rag = RAGPipeline()
    print(f"Вопросов: {len(questions)}\n")

    run(questions, rag, save=args.save)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
