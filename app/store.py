
import chromadb

from app.chunkers.base import Chunk


def _collection_name(provider: str) -> str:
    return f"kb_{provider}"


class VectorStore:
    def __init__(self, chroma_path: str, provider: str):
        self._client = chromadb.PersistentClient(path=chroma_path)
        self._name = _collection_name(provider)
        self._col = self._client.get_or_create_collection(
            name=self._name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def name(self) -> str:
        return self._name

    def reset(self) -> None:
        self._client.delete_collection(self._name)
        self._col = self._client.get_or_create_collection(
            name=self._name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        ids = [
            f"{c.metadata['category']}::{c.metadata['source_file']}::{c.metadata['chunk_index']}"
            for c in chunks
        ]
        documents = [c.text for c in chunks]
        metadatas = []
        for c in chunks:
            m = dict(c.metadata)
            # ChromaDB only supports primitive metadata values
            m["breadcrumbs"] = " > ".join(m.get("breadcrumbs") or [])
            metadatas.append(m)

        self._col.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query(
        self,
        query_vector: list[float],
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        results = self._col.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = 1.0 - dist  # cosine distance → similarity
            if score >= score_threshold:
                hits.append({"text": doc, "metadata": meta, "score": score})
        return hits

    def count(self) -> int:
        return self._col.count()
