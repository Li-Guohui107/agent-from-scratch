# Lesson 04：LangGraph Checkpointer — 让 Agent 记住对话

> Agent 从零开发教程的第四课。沿用第三课的 DeepSeek + `add` / `subtract` / `multiply` 工具，新增会话级记忆与 SQLite 持久化。

## 1. 本课将学会什么

- 使用 `SqliteSaver` 为 LangGraph 添加 Checkpointer。
- 使用 `thread_id` 区分多个独立会话。
- 将消息历史写入本地 SQLite 文件，重启程序后继续同一对话。
- 用 `InMemorySaver` 比较临时内存与磁盘持久化的差别。
- 利用 `get_state()` 查看 Agent 的状态，而不是自己管理对话列表。

**说明**：这是 thread 级别短期记忆，不是跨会话自动检索的长期记忆，也不能无限制地把所有历史塞进模型上下文。项目仅用于本地教学，不是生产环境的多用户服务。

## 2. 目录结构

```text
04_langgraph_memory/
├── main.py            # DeepSeek 多轮对话 Agent
├── test_memory.py     # 离线测试（无需 API Key）
├── requirements.txt   # Python 依赖
├── README.md          # 本教程
├── .env.example       # 配置模板（可公开）
└── .gitignore         # 忽略真实密钥和本地数据库
```

运行后，本地会新增 `chat_history.sqlite` 和可选的 `.venv/`、`.env`，它们已经被 `.gitignore` 忽略，**不要上传**。

## 3. 开始使用（Windows PowerShell）

使用 Python 3.10+，打开终端并进入 `04_langgraph_memory` 目录。

### 3.1 创建环境和安装依赖

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3.2 创建私有配置

```powershell
Copy-Item .env.example .env
notepad .env
```

把 `.env` 里面的 `DEEPSEEK_API_KEY` 改为自己的真实 DeepSeek API Key，别改动公开的 `.env.example`：

```dotenv
DEEPSEEK_API_KEY=这里填写你自己的密钥
DEEPSEEK_MODEL=deepseek-flash
```

请勿将密钥粘贴到截图、README 或提交历史中。

### 3.3 运行

```powershell
.\.venv\Scripts\python.exe main.py
```

默认使用 SQLite，并以 `demo-1` 为当前会话 ID。

```text
你 (demo-1)：计算 20 乘以 5。
Agent：100。

你 (demo-1)：再减去 30。
Agent：70。
```

上述输出仅作示意，模型措辞以及工具调用过程可能不同。

### 3.4 重启后验证记忆

1. 输入 `q` 退出程序。
2. 再次运行 `main.py`，保持同一个会话 ID `demo-1`。
3. 输入 `刚才的结果是多少？`。
4. Agent 将从 SQLite 读取历史状态后回答；可以用 `/history` 验证真实保存的消息。

### 3.5 验证会话隔离

输入 `/thread demo-2`，切换到新会话。此时新会话没有 `demo-1` 的聊天历史。

输入 `/thread demo-1`，切换回之前的会话，使用 `/history` 查看它自己的记录。

## 4. 交互命令

| 命令 | 作用 |
|---|---|
| `问题文本` | 在当前 thread 发送一轮消息 |
| `/history` | 查看当前会话最近 12 条人类/最终 AI 消息 |
| `/state` | 查看累积消息条数与模型调用次数 |
| `/thread demo-2` | 切换会话；若 ID 尚不存在，将创建新会话 |
| `q` 或 `/exit` | 退出 |

命令行参数：

```powershell
# 临时内存模式（重启即失忆）
.\.venv\Scripts\python.exe main.py --storage memory

# 使用 SQLite、指定会话
.\.venv\Scripts\python.exe main.py --storage sqlite --thread demo-2
```

## 5. 为什么它能记住？（本课核心代码）

第三课末尾：

```python
return builder.compile()
```

第四课改成：

```python
return builder.compile(checkpointer=checkpointer)
```

并在每次调用图时，指定相同的会话 ID：

```python
config = {"configurable": {"thread_id": "demo-1"}}
agent.invoke({"messages": [HumanMessage(content="再减去30")]}, config=config)
```

注意：下一轮仅传入**新消息**，不需要手动把所有历史重新作为输入；LangGraph 根据 `thread_id` 找回已保存的 state，`add_messages` 合并新旧消息。如果主动重复传入全部历史，容易造成重复。

保存到磁盘的方式：

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("chat_history.sqlite") as saver:
    graph = builder.compile(checkpointer=saver)
    # 此处使用 graph.invoke(...) / graph.stream(...)
```

需要注意 `with` 的作用域：**完成调用以后再关闭数据库连接**。

## 6. 不需要 API Key 的自动测试

先安装好依赖，然后执行：

```powershell
.\.venv\Scripts\python.exe test_memory.py
```

测试脚本用一个假回复节点代替 DeepSeek，不会调用 API。它依次检查：

1. 同一个 thread A 连续提问两次，历史计数为 1、2。
2. thread B 的第一问仍是 1，证明会话隔离。
3. 关闭并重新打开 SQLite 后，thread A 的下一问计数为 3。

预期输出：

```text
全部测试通过：同会话记忆、不同会话隔离、SQLite 重启后持久化。
```

## 7. 常见问题

**Q：重启后为什么忘了？**

确认使用默认的 `sqlite` 模式、重新启动的是相同目录下的 `main.py`、使用相同 `thread_id`、本地的 `chat_history.sqlite` 没被删除。`--storage memory` 不支持跨重启恢复。

**Q：更换 thread_id 会发生什么？**

新 ID 获取的是另一份会话状态。切回旧 ID 还能恢复旧对话。这是会话隔离，不是登录认证机制；若改造成正式多用户产品，需要服务器自行校验用户对会话 ID 的访问权限。

**Q：每次提问会越来越慢吗？**

可能。历史消息累积后，模型每轮需要处理的上下文也可能变多，成本增加。之后可以学习截断、摘要和长期记忆检索。

**Q：SQLite 是否适合生产环境？**

这是适合单机教学与轻量演示的存储方式。正式的高并发服务应考虑 PostgreSQL 等更健壮的方案。数据库可能包含完整对话和敏感信息，不要直接发布到 GitHub；SQLite 文件本身并不默认加密。

## 8. 练习任务

- [ ] 运行 `test_memory.py`，确认离线测试通过。
- [ ] 在 `demo-1` 连续计算两轮，第二轮能理解“再减去”。
- [ ] 切换到 `demo-2`，验证新对话与原对话互不干扰。
- [ ] 退出、重新运行 `main.py`，确认同一 `thread_id` 的历史被恢复。
- [ ] 尝试 `--storage memory`，比较程序重启后的区别。

## 9. GitHub 提交

将 `04_langgraph_memory/` 放到仓库中的 `tutorials/` 下。只提交本项目六个源码与配置文件，别上传 `.env`、数据库、虚拟环境。如果网页上传不接受点号开头的文件，可以用 **Add file → Create new file** 单独创建 `.env.example` 和 `.gitignore`。

推荐提交信息：

```text
feat: add lesson 04 LangGraph checkpoint memory
```

## 官方参考

- [LangGraph — Add memory](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangGraph — Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph SQLite checkpoint package](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite)
- [DeepSeek API docs](https://api-docs.deepseek.com/)
