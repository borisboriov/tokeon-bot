from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """Send a list of {role, content} messages, return assistant reply."""

    def ask(self, prompt: str) -> str:
        return self.chat([{"role": "user", "content": prompt}])


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per text."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Return embedding for a single query string."""
