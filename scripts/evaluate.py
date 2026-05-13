"""LLM-as-judge evaluation on the golden set.

Usage:
    python scripts/evaluate.py                    # all questions
    python scripts/evaluate.py --group green      # one group
    python scripts/evaluate.py --no-save          # don't write report
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from app.providers import make_llm  # noqa: E402
from app.rag import RAGPipeline     # noqa: E402

_GOLDEN = _ROOT / "data" / "golden_set.json"
_REPORTS = _ROOT / "reports"

_JUDGE_PROMPT = """Ты — эксперт по оценке качества чат-ботов. Оцени ответ бота поддержки.

Вопрос пользователя: {question}
Ожидаемое поведение: {expected_behavior} (answer = дать ответ, refuse = отказать)
Краткий эталонный ответ: {expected_answer}

Ответ бота:
{bot_answer}

Оцени по трём критериям и верни ТОЛЬКО валидный JSON без пояснений:
{{
  "correctness": <1-5>,
  "uses_kb": <true|false>,
  "behavior_correct": <true|false>,
  "comment": "<одна строка>"
}}

Критерии:
- correctness (1–5): насколько ответ соответствует эталону по содержанию
- uses_kb: ссылается ли ответ на конкретные источники из базы знаний (названия файлов, статей, глав)
- behavior_correct: для expected_behavior=refuse — отказал ли бот? для answer — дал ли ответ по существу?"""


def judge_answer(llm, question: str, expected_answer: str,
                 expected_behavior: str, bot_answer: str) -> dict:
    prompt = _JUDGE_PROMPT.format(
        question=question,
        expected_behavior=expected_behavior,
        expected_answer=expected_answer,
        bot_answer=bot_answer,
    )
    raw = llm.ask(prompt)
    # extract JSON from response
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        return {"correctness": 0, "uses_kb": False, "behavior_correct": False,
                "comment": f"parse error: {raw[:100]}"}
    try:
        return json.loads(raw[start:end])
    except json.JSONDecodeError:
        return {"correctness": 0, "uses_kb": False, "behavior_correct": False,
                "comment": f"json error: {raw[:100]}"}


def run(questions: list[dict], rag: RAGPipeline, llm, save: bool) -> dict:
    results = []
    group_stats: dict[str, dict] = {}

    for q in questions:
        qid = q["id"]
        group = q["group"]
        print(f"[{qid}] {q['question'][:60]}...", end=" ", flush=True)

        bot_answer, hits = rag.answer(q["question"])
        sources = [h["metadata"].get("source_file", "") for h in hits]

        verdict = judge_answer(
            llm,
            question=q["question"],
            expected_answer=q["expected_answer"],
            expected_behavior=q["expected_behavior"],
            bot_answer=bot_answer,
        )

        result = {
            "id": qid,
            "group": group,
            "question": q["question"],
            "expected_behavior": q["expected_behavior"],
            "bot_answer": bot_answer,
            "sources": sources,
            **verdict,
        }
        results.append(result)

        mark = "✅" if verdict.get("behavior_correct") else "❌"
        score = verdict.get("correctness", 0)
        print(f"{mark} correctness={score} kb={verdict.get('uses_kb')} | {verdict.get('comment','')[:50]}")

        if group not in group_stats:
            group_stats[group] = {"total": 0, "behavior_ok": 0, "score_sum": 0, "kb_ok": 0}
        gs = group_stats[group]
        gs["total"] += 1
        gs["behavior_ok"] += int(bool(verdict.get("behavior_correct")))
        gs["score_sum"] += verdict.get("correctness", 0)
        gs["kb_ok"] += int(bool(verdict.get("uses_kb")))

    # summary
    print("\n" + "=" * 60)
    print(f"{'Группа':<12} {'Вопросов':>9} {'Поведение':>10} {'Оценка':>8} {'Источники':>11}")
    print("-" * 60)
    total_q = total_ok = total_score = total_kb = 0
    for group in ("green", "yellow", "red"):
        if group not in group_stats:
            continue
        gs = group_stats[group]
        n = gs["total"]
        pct_beh = gs["behavior_ok"] / n * 100
        avg_score = gs["score_sum"] / n
        pct_kb = gs["kb_ok"] / n * 100
        print(f"{group:<12} {n:>9} {pct_beh:>9.0f}% {avg_score:>8.1f} {pct_kb:>10.0f}%")
        total_q += n; total_ok += gs["behavior_ok"]
        total_score += gs["score_sum"]; total_kb += gs["kb_ok"]
    print("-" * 60)
    print(f"{'ИТОГО':<12} {total_q:>9} {total_ok/total_q*100:>9.0f}% "
          f"{total_score/total_q:>8.1f} {total_kb/total_q*100:>10.0f}%")

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total": total_q,
        "behavior_pct": round(total_ok / total_q * 100, 1),
        "avg_correctness": round(total_score / total_q, 2),
        "kb_usage_pct": round(total_kb / total_q * 100, 1),
        "by_group": group_stats,
        "results": results,
    }

    if save:
        _REPORTS.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = _REPORTS / f"eval_{ts}.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nОтчёт сохранён: {out}")

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM-as-judge evaluation on golden set")
    ap.add_argument("--group", help="green | yellow | red")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    questions: list[dict] = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    if args.group:
        questions = [q for q in questions if q["group"] == args.group]
        if not questions:
            print(f"No questions for group {args.group!r}", file=sys.stderr)
            return 1

    print(f"Загружаю RAG pipeline и LLM-судью...")
    rag = RAGPipeline()
    llm = make_llm()
    print(f"Вопросов: {len(questions)}\n")

    run(questions, rag, llm, save=not args.no_save)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
