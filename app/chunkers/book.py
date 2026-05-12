"""BookChunker for the book/ and business_requirements/ categories.

Recursive splitter with "ГЛАВА N" / "Глава N" as the preferred boundary,
falling back to paragraphs and sentences. Sizes target ~400-600 tokens /
50-100 overlap (per plan), ~4 chars/token for Russian.
"""
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.chunkers.base import Chunk, _truncate

_CHUNK_SIZE = 2000   # ~500 tokens
_CHUNK_OVERLAP = 300  # ~75 tokens

_SEPARATORS = [
    "\nГЛАВА ",
    "\nГлава ",
    "\n\n",
    "\n",
    ". ",
    " ",
    "",
]

_CHAPTER_RE = re.compile(r"(ГЛАВА\s+\d+[^\n]*)", re.IGNORECASE)


class BookChunker:
    def __init__(self, category: str = "book"):
        self.category = category
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=_CHUNK_SIZE,
            chunk_overlap=_CHUNK_OVERLAP,
            separators=_SEPARATORS,
            length_function=len,
            keep_separator=True,
        )

    def chunk_file(self, path: Path) -> list[Chunk]:
        text = path.read_text(encoding="utf-8").strip()
        source = path.name
        file_title = _truncate(text.split("\n", 1)[0])

        pieces = self.splitter.split_text(text)
        pieces = self._merge_lone_headers(pieces)

        chunks: list[Chunk] = []
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            chapter = self._find_chapter(piece)
            chunk_title = _truncate(chapter) if chapter else file_title
            crumbs = [self.category, file_title]
            if chapter and chunk_title != file_title:
                crumbs.append(chunk_title)
            chunks.append(Chunk(
                text=piece,
                metadata={
                    "category": self.category,
                    "source_file": source,
                    "title": chunk_title,
                    "breadcrumbs": crumbs,
                    "format": "book",
                    "chunk_index": len(chunks),
                },
            ))
        return chunks

    @staticmethod
    def _find_chapter(text: str) -> str | None:
        m = _CHAPTER_RE.search(text)
        return m.group(1).strip() if m else None

    @staticmethod
    def _merge_lone_headers(pieces: list[str]) -> list[str]:
        """Merge tiny single-line chunks (chapter intros, headers) into the next."""
        merged: list[str] = []
        pending: str | None = None
        for piece in pieces:
            clean = piece.strip()
            is_lone = len(clean) < 250 and "\n\n" not in clean
            if pending is not None:
                merged.append(pending + "\n\n" + piece)
                pending = None
            elif is_lone:
                pending = piece
            else:
                merged.append(piece)
        if pending is not None:
            merged.append(pending)
        return merged
