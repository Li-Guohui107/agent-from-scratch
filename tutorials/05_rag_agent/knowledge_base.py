"""Lesson 04: text chunks -> local embeddings -> Qdrant vector search."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"
COLLECTION = "lesson04_knowledge"


@dataclass(frozen=True)
class Chunk:
    source: str
    number: int
    text: str


def split_text(text: str, size: int = 350, overlap: int = 60) -> list[str]:
    """Simple character windows for this lesson; characters are not tokens."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("切片长度必须为正数，重叠长度必须小于切片长度。")
    text = text.replace("\r\n", "\n").strip()
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        fragment = text[start:end].strip()
        if fragment:
            chunks.append(fragment)
        if end == len(text):
            break
        start = end - overlap
    return chunks


def load_chunks(folder: Path) -> list[Chunk]:
    if not folder.is_dir():
        raise ValueError(f"资料目录不存在：{folder}")
    chunks = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
            continue
        if any(part.startswith(".") for part in path.relative_to(folder).parts):
            continue
        text = path.read_text(encoding="utf-8-sig")
        for number, fragment in enumerate(split_text(text), start=1):
            chunks.append(Chunk(path.relative_to(folder).as_posix(), number, fragment))
    if not chunks:
        raise ValueError("未找到可索引内容，请在 knowledge/ 放入 UTF-8 编码的 .txt 或 .md 文件。")
    return chunks


class KnowledgeBase:
    def __init__(self, model_name: str = DEFAULT_MODEL, root: Path = PROJECT_DIR, embedder=None):
        self.model_name = model_name
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.root / ".rag_index.json"
        self.client = QdrantClient(path=str(self.root / ".qdrant_storage"))
        self._embedder = embedder

    @property
    def embedder(self):
        if self._embedder is None:
            from fastembed import TextEmbedding

            self._embedder = TextEmbedding(
                model_name=self.model_name,
                cache_dir=str(self.root / ".cache" / "fastembed"),
                threads=2,
            )
        return self._embedder

    def index(self, chunks: list[Chunk]) -> int:
        """Rebuild this lesson's collection, keeping original documents intact."""
        if not chunks:
            raise ValueError("不能用空资料重建索引。")
        vectors = [
            [float(value) for value in vector]
            for vector in self.embedder.passage_embed([chunk.text for chunk in chunks])
        ]
        if len(vectors) != len(chunks) or not vectors or not vectors[0]:
            raise ValueError("Embedding 返回的向量数量或维度不正确。")
        dimension = len(vectors[0])
        if any(len(v) != dimension or not all(math.isfinite(x) for x in v) for v in vectors):
            raise ValueError("Embedding 向量维度不一致或含无效数值。")

        # Compute all vectors before replacing the old, reproducible index.
        self.metadata_path.unlink(missing_ok=True)
        if self.client.collection_exists(COLLECTION):
            self.client.delete_collection(COLLECTION)
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
        )
        points = [
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, f"lesson04:{chunk.source}:{chunk.number}:{chunk.text}")),
                vector=vector,
                payload={"source": chunk.source, "chunk": chunk.number, "text": chunk.text},
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        for start in range(0, len(points), 64):
            self.client.upsert(COLLECTION, points=points[start:start + 64], wait=True)
        metadata = {"embedding_model": self.model_name, "dimension": dimension, "chunks": len(points)}
        temporary = self.metadata_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.metadata_path)
        return len(points)

    def search(self, question: str, top_k: int = 3, score_threshold: float = 0.45) -> list[dict]:
        if not question.strip():
            raise ValueError("问题不能为空。")
        if not 1 <= top_k <= 10 or not -1 <= score_threshold <= 1:
            raise ValueError("TOP_K 应在 1-10 之间，SCORE_THRESHOLD 应在 -1 到 1 之间。")
        if not self.metadata_path.exists() or not self.client.collection_exists(COLLECTION):
            raise ValueError("知识库尚未建立或上次建立未完成，请先运行 python ingest.py。")
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if metadata["embedding_model"] != self.model_name:
            raise ValueError("Embedding 模型与现有索引不一致，请重新运行 python ingest.py。")
        vector = [float(v) for v in next(iter(self.embedder.query_embed(question)))]
        if len(vector) != metadata["dimension"]:
            raise ValueError("查询向量维度与索引不一致，请重新建立索引。")
        hits = self.client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True,
        ).points
        return [
            {"source": hit.payload["source"], "chunk": hit.payload["chunk"],
             "text": hit.payload["text"], "score": float(hit.score)}
            for hit in hits
        ]

    def close(self):
        self.client.close()


def print_hits(hits: list[dict]) -> None:
    if not hits:
        print("未找到达到相似度阈值的资料。")
    for number, hit in enumerate(hits, start=1):
        print(f"[{number}] {hit['source']} | 片段 {hit['chunk']} | 相似度 {hit['score']:.3f}")
        print("    " + hit["text"][:180].replace("\n", " "))
