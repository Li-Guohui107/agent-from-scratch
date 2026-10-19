# 第 07 课：FastAPI 部署——RESTful API、接口测试与服务部署

本课把前面学过的 Agent 能力包装成一个可以通过 HTTP 调用的服务，并完成接口测试与部署准备。代码默认可以在**没有大模型 API Key** 的情况下运行；配置 DeepSeek Key 后，`/api/v1/chat` 会调用真实模型。

## 学习目标

- 理解 RESTful API 中的 `GET`、`POST`、`PATCH`、`DELETE`。
- 使用 FastAPI 和 Pydantic 创建接口、校验输入并返回 JSON。
- 通过 Swagger UI、HTTP 请求文件和 `pytest` 测试接口。
- 在本地启动服务，并了解 Docker / 云平台部署的基本流程。
- 知道示例中的内存数据、API Key 和生产环境配置有哪些限制。

## 项目结构

```text
06_fastapi_deployment/
├── main.py              # FastAPI 应用与 RESTful 路由
├── schemas.py           # 请求、响应的数据模型
├── agent.py             # 可选的 DeepSeek 调用；无 Key 时进入演示模式
├── requirements.txt     # 项目依赖
├── .env.example         # 环境变量模板，不含真实密钥
├── .gitignore           # 忽略密钥、虚拟环境和缓存
├── api_examples.http    # 可用 VS Code REST Client 运行的接口示例
├── Dockerfile           # 容器部署示例
└── tests/
    └── test_main.py     # 自动化接口测试
```

## 1. 环境准备（Windows / PowerShell）

建议使用 Python 3.11。打开终端，先进入本课目录 `tutorials/06_fastapi_deployment`，再执行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

如果暂时没有 DeepSeek API Key，可以保持 `.env` 中的 `DEEPSEEK_API_KEY=` 为空，项目仍能启动和测试。若要使用真实模型，请将自己的 Key 填入 `.env`，不要把 `.env` 上传到 GitHub。

## 2. 启动服务

在本课目录运行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

看到 Uvicorn 已启动后，打开以下地址：

- 首页：<http://127.0.0.1:8000/>
- Swagger 接口文档：<http://127.0.0.1:8000/docs>
- ReDoc 接口文档：<http://127.0.0.1:8000/redoc>
- 健康检查：<http://127.0.0.1:8000/api/v1/health>

开发阶段使用 `--reload` 方便修改代码后自动重启；正式部署时不要使用 `--reload`。

## 3. 接口清单

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/` | 查看服务是否启动 |
| `GET` | `/api/v1/health` | 健康检查，供部署平台探测 |
| `POST` | `/api/v1/tasks` | 创建任务 |
| `GET` | `/api/v1/tasks` | 获取任务列表 |
| `GET` | `/api/v1/tasks/{task_id}` | 获取单个任务 |
| `PATCH` | `/api/v1/tasks/{task_id}` | 更新任务部分字段 |
| `DELETE` | `/api/v1/tasks/{task_id}` | 删除任务 |
| `POST` | `/api/v1/chat` | 调用演示 Agent / DeepSeek 模型 |

任务接口用于演示 RESTful 资源操作。当前任务保存在**进程内存**中，服务重启后会清空；它不是生产级数据库。

## 4. 在 Swagger 页面测试接口

打开 <http://127.0.0.1:8000/docs>：

1. 展开 `POST /api/v1/tasks`，点击 **Try it out**。
2. 使用下面的 JSON 创建一个任务，点击 **Execute**。

```json
{
  "title": "完成第六课",
  "description": "学习 FastAPI、接口测试与部署"
}
```

3. 复制返回值中的 `id`，用它测试 `GET /api/v1/tasks/{task_id}`。
4. 用 `PATCH /api/v1/tasks/{task_id}` 发送 `{"completed": true}`。
5. 用 `DELETE /api/v1/tasks/{task_id}` 删除任务。
6. 展开 `POST /api/v1/chat`，发送 `{"message": "请用三点解释 RESTful API"}`。

当没有配置 Key 时，聊天接口会返回演示模式的响应；配置 Key 后会调用 DeepSeek。请求字段错误通常返回 `422`，不存在的任务返回 `404`，上游模型调用失败时返回 `502`。

## 5. 使用 HTTP 请求文件测试

如果使用 VS Code，可以安装 **REST Client** 扩展，然后打开 `api_examples.http`，点击每个请求上方的 **Send Request**。请求可以按创建、查询、更新、删除的顺序依次执行。

## 6. 运行自动化测试

先确保依赖已安装，然后在本课目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

测试使用 FastAPI 的 `TestClient`，不需要启动独立服务，也不需要真实的大模型 API Key。测试覆盖健康检查、任务创建与更新、删除后的 `404`、参数校验以及无 Key 时的聊天演示模式。

## 7. 使用 Docker 运行

请先安装并启动 Docker Desktop。在本课目录执行：

```powershell
docker build -t fastapi-agent-api .
docker run --rm -p 8000:8000 --env-file .env fastapi-agent-api
```

如果没有 `.env` 文件，可先复制 `.env.example` 为 `.env`。随后访问 <http://127.0.0.1:8000/docs>。容器中的服务监听 `0.0.0.0`，这是容器或云平台部署时需要的设置；本地直接开发则可以绑定 `127.0.0.1`。

## 8. 部署到云平台（以 Render 的 Python Web Service 配置为例）

将代码提交到 GitHub 后，在云平台新建 Web Service，并选择你的仓库与分支。因为本课位于子目录，按以下方式配置：

- **Root Directory**：`tutorials/06_fastapi_deployment`
- **Build Command**：`pip install -r requirements.txt`
- **Start Command**：`uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**（如果平台提供）：`/api/v1/health`
- **环境变量**：需要真实模型时再添加 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL`。密钥应填写在平台的环境变量设置中，不要写入代码或提交到仓库。

部署完成后，平台会提供一个公网 HTTPS 地址。用 `https://你的服务域名/docs` 打开接口文档，并通过 `/api/v1/health` 检查服务是否正常。各云平台的控制台字段可能变化，请以所选平台当前界面为准。

也可以选择支持 Docker 的平台，使用本目录的 `Dockerfile` 构建镜像。云平台通常会通过环境变量提供端口，因此 Dockerfile 已支持读取 `PORT`，默认端口为 `8000`。

## 9. RESTful API 的几个要点

- `GET`：读取资源，不应承担创建或删除操作。
- `POST`：创建资源，创建成功通常返回 `201 Created`。
- `PATCH`：只更新请求中提供的字段。
- `DELETE`：删除资源，成功时本示例返回 `204 No Content`。
- `4xx`：通常表示请求或资源问题；`5xx`：通常表示服务端或上游依赖问题。
- Pydantic 会验证请求数据，FastAPI 会自动生成 OpenAPI 文档。

## 10. 安全与生产环境注意事项

1. **不要上传密钥**：只提交 `.env.example`，不要提交 `.env`、API Key 或访问令牌。
2. **不要依赖内存存储**：本示例的任务列表会在重启时丢失；正式项目应换成 SQLite、PostgreSQL 等持久化存储。
3. **配置访问控制**：公开部署前，应按需求添加身份认证、权限控制、限流与日志记录。
4. **保护模型接口**：限制输入长度、控制成本，不要把用户密钥或敏感数据写入日志。
5. **检查跨域需求**：若前端部署在不同域名，需要根据实际前端来源配置 CORS，不要在生产环境无条件开放所有来源。
6. **验证部署结果**：至少检查健康检查、接口文档、错误响应以及日志；不要只凭“部署成功”就认为业务接口正常。

## 本课完成标准

- [ ] 本地可以启动 FastAPI 服务。
- [ ] 能通过 `/docs` 创建、查询、更新和删除任务。
- [ ] `pytest` 测试全部通过。
- [ ] 理解本地端口、`0.0.0.0`、环境变量和公网部署地址的区别。
- [ ] 能在云平台设置启动命令，并验证健康检查接口。
- [ ] 知道何时需要把内存数据替换成数据库。

