"""Build the local knowledge index. No DeepSeek API key is needed."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from knowledge_base import DEFAULT_MODEL, PROJECT_DIR, KnowledgeBase, load_chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="将 .txt/.md 资料切片、向量化并写入 Qdrant")
    parser.add_argument("--data", type=Path, default=PROJECT_DIR / "knowledge", help="知识库资料目录")
    args = parser.parse_args()
    load_dotenv(PROJECT_DIR / ".env")
    kb = None
    try:
        chunks = load_chunks(args.data)
        print(f"读取 {len({chunk.source for chunk in chunks})} 个文件，得到 {len(chunks)} 个片段。")
        print("正在生成中文向量；首次运行需要联网下载 Embedding 模型，请等待。")
        kb = KnowledgeBase(model_name=os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL))
        count = kb.index(chunks)
        print(f"索引建立成功：{count} 个片段已写入 Qdrant 本地存储。")
        return 0
    except Exception as exc:
        print(f"建立索引失败：{type(exc).__name__}: {exc}")
        return 1
    finally:
        if kb is not None:
            kb.close()


if __name__ == "__main__":
    raise SystemExit(main())
