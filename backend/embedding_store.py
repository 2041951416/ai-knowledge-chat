"""语义向量存储（基于 ChromaDB + ONNX 嵌入）"""
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from backend.config import CHROMA_DB_PATH


class VectorStore:
    def __init__(self, persist_dir: str = None):
        db_path = Path(persist_dir or CHROMA_DB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(
            name="docs",
            embedding_function=DefaultEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, chunks: list[str], metadata: list[dict] | None = None):
        """增量添加文档块"""
        if not chunks:
            return 0
        metadatas = metadata or [{} for _ in chunks]
        # 避免 ID 冲突：用时间戳后缀
        import time
        base = int(time.time() * 1000)
        ids = [f"doc_{base}_{i}" for i in range(len(chunks))]
        # 分批添加（避免单批太大）
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            end = i + batch_size
            self.collection.add(
                documents=chunks[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        count = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
        )
        docs = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "content": doc,
                    "score": round(1 - results["distances"][0][i], 4) if results.get("distances") else 0,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                })
        return docs

    def count(self) -> int:
        return self.collection.count()

    def clear(self):
        try:
            self.client.delete_collection("docs")
        except ValueError:
            pass
        self.collection = self.client.get_or_create_collection(
            name="docs",
            embedding_function=DefaultEmbeddingFunction(),
        )

    def delete_by_source(self, source_name: str):
        """删除指定来源文件的所有块"""
        self.collection.delete(where={"source": source_name})

    def get_all_sources(self) -> list[str]:
        """获取所有来源文件列表"""
        try:
            results = self.collection.get(include=["metadatas"])
            sources = set()
            if results["metadatas"]:
                for m in results["metadatas"]:
                    if m.get("source"):
                        sources.add(m["source"])
            return sorted(sources)
        except Exception:
            return []


_store = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
