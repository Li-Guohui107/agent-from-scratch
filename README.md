# 🤖 Agent From Scratch

<div align="center">

### 从零开始构建 AI Agent

**一份面向 Python 开发者的 AI Agent 中文开源教程**

从大模型 API、Tool Calling，到 LangGraph、RAG 和智能体工程化部署。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-Planned-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Planned-purple)
![RAG](https://img.shields.io/badge/RAG-Planned-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**[快速开始](#-快速开始) · [学习路线](#-学习路线) · [项目目录](#-项目目录) · [参与贡献](#-参与贡献)**

</div>

---

## 📖 项目介绍

大语言模型能够理解自然语言、生成文本和代码，但要让它真正完成任务，仅依赖一次模型调用往往是不够的。

例如，让 AI 查询数据库、检索知识库、调用外部接口，或根据任务状态决定下一步操作，都需要额外的工具、控制逻辑和工程设计。

**Agent From Scratch** 是一个持续更新的 AI Agent 中文开源学习项目。

这个仓库不会一开始就堆砌复杂框架，而是从基础 Python 代码出发，逐步理解智能体的核心机制，再将这些机制应用到实际项目中。

我们的目标是：

- **理解原理**：不仅知道怎么调用 API，更要理解 Agent 的工作机制。
- **代码实践**：每一期提供独立示例，尽可能降低学习和复现成本。
- **逐步进阶**：从 Tool Calling 发展到状态机、RAG 和复杂工作流。
- **面向工程**：关注错误处理、工具安全、日志、测试和部署。
- **中文分享**：使用清晰的中文解释概念与核心代码。

---

## 🧭 学习路线

| 阶段 | 教程主题 | 核心内容 | 状态 |
|---|---|---|---|
| 01 | Tool Calling 入门 | 大模型调用 Python 函数 | 已完成 |
| 02 | 多工具 Agent | 工具选择与执行循环 | 已完成 |
| 03 | LangGraph 基础 | State、Node、Edge、条件路由 | 已完成 |
| 04 | RAG 知识库 Agent | Embedding、向量检索、Qdrant | 已完成 |
| 05 | SQL Agent | 自然语言查询数据库 | 📅 计划中 |
| 06 | FastAPI 部署 | RESTful API、接口测试与服务部署 | 📅 计划中 |

> 项目将根据实际开发进度持续更新。标记为计划中的功能尚未实现。

---

## 📂 项目目录

```text
agent-from-scratch/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
│
└── tutorials/
    └── 01_tool_calling/
        ├── main.py
        └── README.md
```

其中：

- `tutorials/` 存放各阶段的教学代码。
- `main.py` 是对应章节的可运行示例。
- 每个章节的 `README.md` 用于解释原理、运行步骤和代码逻辑。
- `.env.example` 用于说明环境变量的配置方式。

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Li-Guohui107/agent-from-scratch.git
cd agent-from-scratch
```

也可以在 GitHub 页面点击 `Code → Download ZIP` 下载项目。

### 2. 环境要求

建议使用：

- Python 3.10 或更新版本
- Git
- VS Code 或其他 Python 开发工具
- 有效的 DeepSeek API Key

### 3. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 4. 配置 API Key

在 DeepSeek 开放平台创建 API Key。

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
```

Linux / macOS：

```bash
export DEEPSEEK_API_KEY="your_api_key"
```

请不要将真实 API Key 提交到 GitHub。

### 5. 运行第一个 Agent

```bash
python tutorials/01_tool_calling/main.py
```

输入：

```text
你：请使用乘法工具计算125乘以8。
```

预期工具调用过程：

```text
[Tool] multiply: {'a': 125, 'b': 8} -> 1000
Agent：125乘以8等于1000。
```

上述内容是预期输出示例，实际输出取决于模型响应。

---

## 🧠 核心知识点

本项目主要围绕以下技术展开。

**LLM API**

学习大模型接口调用、消息结构、上下文管理和基本参数配置。

**Tool Calling**

理解模型如何选择工具、生成参数，以及程序如何真正执行工具调用。

**LangChain / LangGraph**

学习智能体框架、状态管理、条件路由、执行流程以及任务控制。

**RAG**

使用向量数据库和文档检索技术，让 Agent 能够基于外部知识回答问题。

**FastAPI**

将智能体封装成 HTTP 服务，便于前端系统和其他业务系统调用。

---

## 🔬 后续实战项目

未来计划增加具有实际应用价值的项目，包括：

- SQL Agent：使用自然语言查询结构化数据库。
- Knowledge Base Agent：基于 Qdrant 的企业知识库助手。
- Workflow Agent：基于 LangGraph 的多步骤工作流。
- API Agent：通过 FastAPI 提供智能体服务接口。

这些项目将逐步补充代码、教程和测试说明。

---

## 🤝 参与贡献

欢迎对 AI Agent 技术感兴趣的开发者交流、学习和参与改进。

如果你发现代码存在问题，或者有新的教程建议，可以通过 GitHub Issues 提出。

欢迎提交 Pull Request，一起完善这个项目。

---

## 📜 开源协议

本项目采用 [MIT License](LICENSE)。

你可以在遵守 MIT 协议的前提下学习、使用和修改本项目代码。

---

## ⭐ 支持项目

如果这个项目对你的 AI Agent 学习有所帮助，欢迎给仓库点一个 Star。

持续学习，持续实践，从零开始构建真正能够解决问题的 AI Agent。
