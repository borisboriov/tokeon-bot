from pathlib import Path

from app.chunkers.base import Chunk
from app.chunkers.book import BookChunker
from app.chunkers.faq import FAQChunker
from app.chunkers.legal import LegalChunker


def chunk_by_category(file_path: Path, category: str) -> list[Chunk]:
    """Pick the right chunker for the given top-level KB category."""
    if category == "instructions":
        return FAQChunker(category=category).chunk_file(file_path)
    if category == "law":
        return LegalChunker(category=category).chunk_file(file_path)
    if category in ("book", "business_requirements"):
        return BookChunker(category=category).chunk_file(file_path)
    raise ValueError(f"Unknown category: {category}")


__all__ = ["Chunk", "FAQChunker", "LegalChunker", "BookChunker", "chunk_by_category"]
