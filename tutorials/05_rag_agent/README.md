# 第五课：RAG 知识库 Agent

本课对应课程表中的 **04 | RAG 知识库 Agent | Embedding、向量检索、Qdrant**。

在第三课认识 Agent 工作流以后，这一课给助手接入自己的资料：先检索相关原文，再让 DeepSeek 根据原文回答，并显示文件名和片段编号。项目以固定的“检索 → 生成”工作流实现，便于看清 RAG 的每一步。

## 1. 本课目标

- 读取本地 UTF-8 编码的 `.txt`、`.md` 文件。
- 把文档切成带重叠的片段，保留来源信息。
- 用中文 Embedding 模型把片段和问题转换成向量。
- 用 Qdrant 的余弦相似度检索相关片段，观察 Top K 和阈值。
- 把片段交给 DeepSeek，生成附资料编号的回答。

| 部件 | 本课选择 | 负责什么 |
|---|---|---|
| Embedding | FastEmbed + `BAAI/bge-small-zh-v1.5` | 在本地把中文文本变成向量，默认 512 维 |
| 向量数据库 | Qdrant Local | 保存向量、原文及来源，按相似度检索 |
| 回答模型 | DeepSeek | 阅读检索出的片段，组织中文答案 |
| 工作流 | LangGraph | 依次执行检索和生成两个节点 |

使用 Qdrant 官方 Python 客户端的本地模式，无需 Docker 或云账号；这是开发与教学模式。Embedding 在本机运行。生成答案时，问题和检索出的片段会发送给 DeepSeek API。

## 2. 文件说明

| 文件或目录 | 作用 |
|---|---|
| `knowledge_base.py` | 文档读取、切片、Embedding、Qdrant 写入与检索 |
| `ingest.py` | 导入资料并建立向量索引 |
| `main.py` | 检索与问答入口 |
| `test_rag.py` | 无需密钥、无需下载模型的结构测试 |
| `knowledge/` | 三份中文教学资料 |
| `requirements.txt` | Python 依赖 |
| `.env.example` | 公开配置模板 |
| `.gitignore` | 排除密钥、模型缓存和本地索引 |

运行后生成 `.qdrant_storage/`、`.rag_index.json`、`.cache/`；它们都不需要提交到 GitHub。

## 3. Windows 快速开始

建议使用 Python 3.11 或 3.12。解压后进入 `05_rag_agent` 文件夹，在该文件夹打开 PowerShell。以下命令都在这个目录中运行。

### 3.1 创建环境、安装依赖

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3.2 先运行不需要密钥的测试

```powershell
.\.venv\Scripts\python.exe test_rag.py
```

预期六项测试通过，末尾显示 `OK`。测试使用真实的 Qdrant 本地存储，但用固定测试向量和假模型回复替代真实模型。它验证切片、来源、阈值、索引持久化、更新清理和工作流，不代表真实语义检索质量已经得到评测。

### 3.3 创建本地配置

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` 内容：

```dotenv
DEEPSEEK_API_KEY=这里替换成你自己的真实密钥
DEEPSEEK_MODEL=deepseek-flash
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
TOP_K=3
SCORE_THRESHOLD=0.45
```

先只做导入和检索时，密钥可以继续使用模板中的占位符；真正生成答案时再填写。真实密钥仅放在本地 `.env`。代码以非思考模式调用 DeepSeek，便于集中学习 RAG。

### 3.4 建立知识库

```powershell
.\.venv\Scripts\python.exe ingest.py
```

首次运行 FastEmbed 会联网下载中文模型，下载时间取决于网络；后续使用本地缓存。CPU 即可运行。下载失败时先排查模型下载网络，不要把问题当成 DeepSeek 密钥错误；下载错误会显示在终端。

成功后显示索引片段数量。默认模型为 512 维，代码读取模型实际输出的维度来创建集合，不手写固定维度。

### 3.5 先观察检索，不调用大模型

```powershell
.\.venv\Scripts\python.exe main.py --retrieve-only --question "客户月报应该包含哪几部分？"
```

程序应输出相关文件名、片段编号、相似度分数和原文摘要。先检查取回的资料是否能回答问题，再进入生成环节。

### 3.6 开始问答

在本地 `.env` 填好密钥，保存后运行：

```powershell
.\.venv\Scripts\python.exe main.py
```

可依次尝试：

```text
客户月报应该包含哪几部分？
现场作业记录需要包含哪些信息？
示例公司要求作业后多久整理记录？
Embedding、Qdrant 和 DeepSeek 分别做什么？
资料有没有规定具体药剂配比？
```

回答前会显示检索来源，正文中的 `[1]`、`[2]` 对应本轮来源编号。每次提问独立检索资料。输入 `q` 退出。

月报问题的示意回答为：月报包括风险评估、作业内容、现场影像、效果评估、总结和下月计划。[1]

具体措辞和编号以实际检索结果为准。`knowledge/` 中的项目规定是教学设定，不能当作行业标准或真实合同要求。

## 4. 按顺序读懂代码

### 4.1 切片

`load_chunks()` 读取资料，`split_text()` 默认按 350 个字符切片，相邻片段重叠 60 个字符。重叠有助于减少段落边界的信息丢失。这是教学用的字符窗口，字符数不等于 token 数；长英文、表格或复杂文档需要更合适的切分方法。

每个片段保留 `source`、`number`、`text`，所以检索后可以追溯原文。

### 4.2 Embedding

```python
vectors = list(embedder.passage_embed(document_chunks))
query_vector = next(iter(embedder.query_embed(question)))
```

文档和问题使用同一个模型。Embedding 生成向量，不会回答问题，也不是训练 DeepSeek。

### 4.3 写入 Qdrant

```python
client = QdrantClient(path=".qdrant_storage")
client.create_collection(
    collection_name="lesson04_knowledge",
    vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
)
```

一个 point 包括 ID、向量和 payload；payload 保存原文、文件名和片段编号。实际代码把路径固定到项目目录，因此从别的工作目录启动也能找到同一份索引。

### 4.4 向量检索

```python
hits = client.query_points(
    collection_name="lesson04_knowledge",
    query=query_vector,
    limit=3,
    score_threshold=0.45,
    with_payload=True,
).points
```

Top K 是最多返回多少个片段，阈值是是否保留片段的门槛。余弦相似度不是答案正确率；本课默认的 `0.45` 只是练习起点，需要结合真实问题校准。

### 4.5 检索后生成

`main.py` 中的 LangGraph 先执行 `retrieve`，再执行 `answer`。`answer` 把用户问题和检索片段交给模型，要求依据资料回答并标注编号。没有任何结果超过阈值时，程序直接返回资料不足，不调用 DeepSeek。

取回的片段即使相似，也可能没有答案，因此提示词还要求模型说明资料不足。这些做法减少无依据回答，不能保证完全消除错误；可通过显示的原文核查结论和引用。

## 5. 更新资料与模型

把自己的 `.txt` 或 `.md` 文件放入 `knowledge/`，再执行 `ingest.py`。也可以保持私有资料在仓库外：

```powershell
.\.venv\Scripts\python.exe ingest.py --data "D:\my_knowledge"
```

每次导入都会重建本课的 `lesson04_knowledge` 集合，清理旧片段，原始文件保持原样。更新、删除资料后都应重新导入。更换 Embedding 模型后也必须重新导入，即使两个模型的维度相同；程序会检查模型是否与索引一致。

Qdrant 本地目录一次由一个进程打开：导入完成退出后，再启动问答；不要在两个终端同时占用同一目录。

本课读取 `.txt/.md`。PDF 和 Word 先提取为文本，再放入知识库；正文中保留标题和出处会更有利于核查。

## 6. GitHub 提交

放到已有仓库的 `tutorials/04_rag_agent/`。先解压，再上传源码、README、依赖和三份示例资料。网页上传不接受点号文件时，用 **Add file → Create new file** 手动创建 `.env.example` 和 `.gitignore`，内容复制本课程包的对应文件。

只公开配置模板和教学资料。真实 `.env`、私有文档、`.venv/`、模型缓存及本地索引不应通过网页手动上传；网页上传需要自行选择正确文件。

提交说明：

```text
feat: add lesson 04 RAG knowledge agent with Qdrant
```

课程表可在代码上传后改成“已上传”，本地运行验证后再改成“已完成”：

```markdown
| 04 | RAG 知识库 Agent | Embedding、向量检索、Qdrant | ✅ 已完成 |
```

## 7. 完成本课的检查项

- [ ] 六项离线测试全部通过。
- [ ] 成功将三份示例资料写入 Qdrant。
- [ ] 只检索模式取回的原文能回答月报问题。
- [ ] DeepSeek 的回答包含可对应原文的编号。
- [ ] 询问资料之外的问题，检查是否明确说明资料不足。
- [ ] 修改一份资料并重新导入，检查新内容能被取回。
- [ ] 将 `TOP_K` 分别改成 1 和 3，观察上下文变化。

## 8. 本课程包的验证情况

2026-10-15 在 Python 3.12 环境验证：六项离线测试通过；真实中文 Embedding 模型下载和索引建立通过；月报、现场记录、RAG 概念三个问题均能取回对应资料；示例营业收入问题没有结果超过默认阈值。使用的版本包括 Qdrant Client 1.19.1、FastEmbed 0.9.0、LangGraph 1.2.15 和 langchain-openai 1.7.2。

未使用真实 DeepSeek 密钥进行在线生成测试；在线生成需在本地配置密钥后验证。这里的示例检索检查覆盖范围有限，不是对任意知识库的效果保证。

## 官方参考

- [Qdrant Python Client：Local mode 与向量检索](https://github.com/qdrant/qdrant-client)
- [Qdrant Quickstart：集合、向量写入与查询](https://qdrant.tech/documentation/quickstart/)
- [FastEmbed 支持的模型：中文 BGE-small](https://qdrant.github.io/fastembed/examples/Supported_Models/)
- [FastEmbed 官方文档](https://qdrant.github.io/fastembed/)
- [DeepSeek 模型列表](https://api-docs.deepseek.com/api/list-models/)
- [DeepSeek 思考模式参数](https://api-docs.deepseek.com/guides/thinking_mode/)
