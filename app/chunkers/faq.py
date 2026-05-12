"""Chunker for the instructions/ category of the KB.

Detects one of three layouts per file and applies the right strategy:
  - faq:       "Вопрос: ... \\n Ответ: ..." pairs split by blank lines (often.questions.txt)
  - glossary:  one term per line, "Term — Definition" (terminology.txt, jargon.txt)
  - procedure: title + steps, possibly with multiple sub-sections (wallet.txt etc.)
"""
import re
from pathlib import Path

from app.chunkers.base import Chunk, _truncate

_Q_RE = re.compile(r"^Вопрос:\s*", re.MULTILINE)
_A_RE = re.compile(r"^Ответ:\s*", re.MULTILINE)
_BLANK_RE = re.compile(r"\n\s*\n")
_GLOSSARY_LINE_RE = re.compile(r"^(?P<term>.+?)\s+[—–\-]\s+(?P<defn>.+)$")


class FAQChunker:
    """Chunker for instructions/*.txt files. Picks layout per file."""

    def __init__(self, category: str = "instructions"):
        self.category = category

    def chunk_file(self, path: Path) -> list[Chunk]:
        text = path.read_text(encoding="utf-8").strip()
        source = path.name
        layout = self._detect_layout(text)
        if layout == "faq":
            return self._chunk_faq(text, source)
        if layout == "glossary":
            return self._chunk_glossary(text, source)
        return self._chunk_procedure(text, source)

    def _detect_layout(self, text: str) -> str:
        if len(_Q_RE.findall(text)) >= 3:
            return "faq"
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if len(lines) >= 5:
            matched = sum(1 for ln in lines if _GLOSSARY_LINE_RE.match(ln))
            if matched / len(lines) >= 0.7:
                return "glossary"
        return "procedure"

    def _chunk_faq(self, text: str, source: str) -> list[Chunk]:
        first_line = text.split("\n", 1)[0].strip()
        if first_line.startswith("Вопрос:"):
            file_title = "Частые вопросы"
            body = text
        else:
            file_title = _truncate(first_line.rstrip("."))
            body = text[len(first_line):].lstrip()

        chunks: list[Chunk] = []
        for block in _BLANK_RE.split(body):
            block = block.strip()
            if not block:
                continue
            q_match = _Q_RE.match(block)
            if not q_match:
                continue
            a_match = _A_RE.search(block)
            if a_match:
                question = block[q_match.end():a_match.start()].strip()
                answer = block[a_match.end():].strip()
                chunk_text = f"Вопрос: {question}\nОтвет: {answer}"
            else:
                question = block[q_match.end():].strip()
                chunk_text = f"Вопрос: {question}"
            title = self._short_title(question)
            chunks.append(Chunk(
                text=chunk_text,
                metadata={
                    "category": self.category,
                    "source_file": source,
                    "title": title,
                    "breadcrumbs": [self.category, file_title, title],
                    "format": "faq",
                    "chunk_index": len(chunks),
                },
            ))
        return chunks

    def _chunk_glossary(self, text: str, source: str) -> list[Chunk]:
        file_title = _truncate(
            source.removesuffix(".txt").replace("_", " ").replace(".", " ").strip().capitalize()
        )
        chunks: list[Chunk] = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            m = _GLOSSARY_LINE_RE.match(line)
            term = m.group("term").strip() if m else line
            title = _truncate(term)
            chunks.append(Chunk(
                text=line,
                metadata={
                    "category": self.category,
                    "source_file": source,
                    "title": title,
                    "breadcrumbs": [self.category, file_title, title],
                    "format": "glossary",
                    "chunk_index": len(chunks),
                },
            ))
        return chunks

    def _chunk_procedure(self, text: str, source: str) -> list[Chunk]:
        sections = [s.strip() for s in _BLANK_RE.split(text) if s.strip()]
        if not sections:
            return []

        file_title = _truncate(sections[0].split("\n", 1)[0])

        if len(sections) == 1:
            return [Chunk(
                text=text.strip(),
                metadata={
                    "category": self.category,
                    "source_file": source,
                    "title": file_title,
                    "breadcrumbs": [self.category, file_title],
                    "format": "procedure",
                    "chunk_index": 0,
                },
            )]

        chunks: list[Chunk] = []
        for section in sections:
            section_title = _truncate(section.split("\n", 1)[0])
            crumbs = [self.category, file_title]
            if section_title != file_title:
                crumbs.append(section_title)
            chunks.append(Chunk(
                text=section,
                metadata={
                    "category": self.category,
                    "source_file": source,
                    "title": section_title,
                    "breadcrumbs": crumbs,
                    "format": "procedure",
                    "chunk_index": len(chunks),
                },
            ))
        return chunks

    @staticmethod
    def _short_title(question: str, max_len: int = 80) -> str:
        """Take the first variant of a multi-part question, trim to max_len."""
        first = question.split("?", 1)[0].strip()
        if "?" in question and first:
            first += "?"
        elif not first:
            first = question
        if len(first) > max_len:
            first = first[:max_len - 3] + "..."
        return first
