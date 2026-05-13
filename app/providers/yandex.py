from app.providers.base import EmbeddingProvider, LLMProvider


class YandexLLM(LLMProvider):
    def __init__(self, api_key: str, folder_id: str, model: str):
        self._api_key = api_key
        self._folder_id = folder_id
        self._model = model

    def chat(self, messages: list[dict]) -> str:
        from yandex_cloud_ml_sdk import YCloudML

        sdk = YCloudML(folder_id=self._folder_id, auth=self._api_key)
        yc_messages = [
            {"role": m["role"], "text": m["content"]}
            for m in messages
        ]
        result = sdk.models.completions(self._model).run(yc_messages)
        return result.alternatives[0].message.text


class YandexEmbeddings(EmbeddingProvider):
    def __init__(self, api_key: str, folder_id: str, model: str):
        self._api_key = api_key
        self._folder_id = folder_id
        self._model = model

    def _sdk(self):
        from yandex_cloud_ml_sdk import YCloudML
        return YCloudML(folder_id=self._folder_id, auth=self._api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._sdk().models.text_embeddings(self._model)
        return [model.run(t).embedding for t in texts]

    def embed_query(self, text: str) -> list[float]:
        # queries use a separate "text-search-query" model for better results
        model = self._sdk().models.text_embeddings("text-search-query")
        return model.run(text).embedding
