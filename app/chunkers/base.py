"""Shared types and helpers for KB chunkers."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: dict


_MAX_TITLE_LEN = 80


def _truncate(s: str, max_len: int = _MAX_TITLE_LEN) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[:max_len - 3].rstrip() + "..."
