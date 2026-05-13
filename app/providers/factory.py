from app.config import settings
from app.providers.base import EmbeddingProvider, LLMProvider


def make_llm() -> LLMProvider:
    if settings.llm_provider == "gigachat":
        from app.providers.gigachat import GigaChatLLM
        return GigaChatLLM(
            credentials=settings.gigachat_credentials,
            scope=settings.gigachat_scope,
            model=settings.gigachat_model,
            verify_ssl_certs=settings.gigachat_verify_ssl_certs,
        )
    if settings.llm_provider == "yandex":
        from app.providers.yandex import YandexLLM
        return YandexLLM(
            api_key=settings.yandex_api_key,
            folder_id=settings.yandex_folder_id,
            model=settings.yandex_model,
        )
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider!r}")


def make_embeddings() -> EmbeddingProvider:
    if settings.embedding_provider == "local":
        from app.providers.local import LocalEmbeddingProvider
        return LocalEmbeddingProvider(model_name=settings.local_embedding_model)
    if settings.embedding_provider == "gigachat":
        from app.providers.gigachat import GigaChatEmbeddings
        return GigaChatEmbeddings(
            credentials=settings.gigachat_credentials,
            scope=settings.gigachat_scope,
            model=settings.gigachat_embedding_model,
            verify_ssl_certs=settings.gigachat_verify_ssl_certs,
        )
    if settings.embedding_provider == "yandex":
        from app.providers.yandex import YandexEmbeddings
        return YandexEmbeddings(
            api_key=settings.yandex_api_key,
            folder_id=settings.yandex_folder_id,
            model=settings.yandex_embedding_model,
        )
    raise ValueError(f"Unknown embedding provider: {settings.embedding_provider!r}")
