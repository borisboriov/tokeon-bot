"""LegalChunker for the law/ category (incl. law/documents/).

Recursive splitter tuned for the "Статья N." article-boundary pattern seen
in 259-FZ, 115-FZ and platform regulations. Falls back to paragraph/sentence
splits in files without article markers.

Sizes target ~800-1000 tokens / 100-150 overlap (per plan), approximated as
chars at ~4 chars/token for Russian text.
"""
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.chunkers.base import Chunk, _truncate

_CHUNK_SIZE = 3600   # ~900 tokens
_CHUNK_OVERLAP = 500  # ~125 tokens

_SEPARATORS = [
    "\nСтатья ",
    "\nГлава ",
    "\n\n",
    "\n",
    ". ",
    " ",
    "",
]

_ARTICLE_RE = re.compile(r"(Статья\s+\d+(?:\.\d+)?\.?[^\n]*)")
_CHAPTER_RE = re.compile(r"(Глава\s+\d+[^\n]*)", re.IGNORECASE)


class LegalChunker:
    def __init__(self, category: str = "law"):
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
            article = self._find_header(piece)
            chunk_title = _truncate(article) if article else file_title
            crumbs = [self.category, file_title]
            if article and chunk_title != file_title:
                crumbs.append(chunk_title)
            chunks.append(Chunk(
                text=piece,
                metadata={
                    "category": self.category,
                    "source_file": source,
                    "title": chunk_title,
                    "breadcrumbs": crumbs,
                    "format": "legal",
                    "chunk_index": len(chunks),
                },
            ))
        return chunks

    @staticmethod
    def _find_header(text: str) -> str | None:
        m = _ARTICLE_RE.search(text)
        if m:
            return m.group(1).strip()
        m = _CHAPTER_RE.search(text)
        return m.group(1).strip() if m else None

    @staticmethod
    def _merge_lone_headers(pieces: list[str]) -> list[str]:
        """Merge tiny single-line chunks (article headers, stub markers, doc titles)
        into the next chunk so they travel with related content."""
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
