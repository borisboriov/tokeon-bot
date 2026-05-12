from gigachat import GigaChat

from app.providers.base import EmbeddingProvider, LLMProvider


class GigaChatLLM(LLMProvider):
    def __init__(self, credentials: str, scope: str, model: str, verify_ssl_certs: bool):
        self._credentials = credentials
        self._scope = scope
        self._model = model
        self._verify = verify_ssl_certs

    def chat(self, messages: list[dict]) -> str:
        from gigachat.models import Chat, Messages, MessagesRole

        role_map = {"user": MessagesRole.USER, "assistant": MessagesRole.ASSISTANT}
        gc_messages = [
            Messages(role=role_map.get(m["role"], MessagesRole.USER), content=m["content"])
            for m in messages
        ]
        payload = Chat(messages=gc_messages, model=self._model)

        with GigaChat(
            credentials=self._credentials,
            scope=self._scope,
            verify_ssl_certs=self._verify,
        ) as client:
            response = client.chat(payload)
        return response.choices[0].message.content


class GigaChatEmbeddings(EmbeddingProvider):
    """Requires paid GigaChat plan. Raises NotImplementedError on free tier (402)."""

    def __init__(self, credentials: str, scope: str, model: str, verify_ssl_certs: bool):
        self._credentials = credentials
        self._scope = scope
        self._model = model
        self._verify = verify_ssl_certs

    def _client(self) -> GigaChat:
        return GigaChat(
            credentials=self._credentials,
            scope=self._scope,
            verify_ssl_certs=self._verify,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        with self._client() as client:
            response = client.embeddings(texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
