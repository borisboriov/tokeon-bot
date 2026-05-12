from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "gigachat"
    embedding_provider: str = "local"

    kb_path: str = "data/knowledge_base"
    chroma_path: str = "data/chroma"

    top_k: int = 5
    retrieval_score_threshold: float = 0.3

    # GigaChat
    gigachat_credentials: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat"
    gigachat_embedding_model: str = "Embeddings"
    gigachat_verify_ssl_certs: bool = False

    # YandexGPT
    yandex_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_model: str = "yandexgpt-lite"
    yandex_embedding_model: str = "text-search-doc"

    # Local embeddings
    local_embedding_model: str = "intfloat/multilingual-e5-small"


settings = Config()
