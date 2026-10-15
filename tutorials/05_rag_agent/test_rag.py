"""Offline structural tests: real local Qdrant, deterministic fake embeddings/LLM."""

import tempfile
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage

from knowledge_base import Chunk, KnowledgeBase, load_chunks, split_text
from main import build_agent


class FakeEmbedding:
    @staticmethod
    def vector(text):
        if "月报" in text:
            return [1.0, 0.0, 0.0]
        if "记录" in text:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def passage_embed(self, texts):
        return iter(self.vector(text) for text in texts)

    def query_embed(self, text):
        return iter([self.vector(text)])


class FakeLLM:
    calls = 0

    def invoke(self, messages):
        self.calls += 1
        content = messages[-1].content
        assert "用户问题" in content and "[1] 来源：report.md" in content
        assert "风险评估" in content
        return AIMessage(content="月报包括风险评估等六个部分。[1]")


class RagTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.kb = KnowledgeBase(root=self.root, embedder=FakeEmbedding())
        self.kb.index([
            Chunk("report.md", 1, "月报包括风险评估、作业内容、现场影像、效果评估、总结和下月计划。"),
            Chunk("records.md", 1, "现场记录包含日期、人员和具体点位。"),
        ])

    def tearDown(self):
        self.kb.close()
        self.temp.cleanup()

    def test_chunking_and_loading(self):
        self.assertEqual(split_text("abcdefghij", size=6, overlap=2), ["abcdef", "efghij"])
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "a.txt").write_text("示例资料", encoding="utf-8")
        (docs / "ignored.csv").write_text("不应读取", encoding="utf-8")
        self.assertEqual(load_chunks(docs), [Chunk("a.txt", 1, "示例资料")])

    def test_top_k_sources_and_threshold(self):
        hits = self.kb.search("月报", top_k=1, score_threshold=0.8)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["source"], "report.md")
        self.assertEqual(self.kb.search("无关问题", score_threshold=0.8), [])

    def test_restart_preserves_index(self):
        self.kb.close()
        self.kb = KnowledgeBase(root=self.root, embedder=FakeEmbedding())
        self.assertEqual(self.kb.search("记录")[0]["source"], "records.md")

    def test_reindex_removes_stale_chunks(self):
        self.kb.index([Chunk("new.md", 1, "新的月报规定。")])
        self.assertEqual(self.kb.search("月报")[0]["source"], "new.md")
        self.assertEqual(self.kb.search("记录", score_threshold=0.8), [])

    def test_model_mismatch_requires_reindex(self):
        self.kb.model_name = "another-model-with-the-same-dimension"
        with self.assertRaisesRegex(ValueError, "模型与现有索引不一致"):
            self.kb.search("月报")

    def test_workflow_uses_retrieved_context(self):
        llm = FakeLLM()
        graph = build_agent(self.kb, llm, score_threshold=0.8)
        result = graph.invoke({"question": "月报包含哪些内容？"})
        self.assertIn("[1]", result["answer"])
        self.assertEqual(llm.calls, 1)
        result = graph.invoke({"question": "无关问题"})
        self.assertIn("资料不足", result["answer"])
        self.assertEqual(llm.calls, 1)  # No context: do not call the model.


if __name__ == "__main__":
    unittest.main(verbosity=2)
