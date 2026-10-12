# Lesson 02: Multi-Tool Agent（多工具智能体）

## 📖 项目介绍

本项目是 **Agent From Scratch** 系列教程的第二课。

第一课中，我们学习了如何通过大语言模型调用单个 Python 工具。本节课将在此基础上，实现一个支持多个工具、自动选择工具和多轮执行的简单 Agent。

本项目使用 Python 和 DeepSeek API，不依赖 LangChain 或 LangGraph 等 Agent 框架，帮助初学者理解智能体的基本工作机制。

## 🎯 学习目标

完成本节课后，你将掌握：

1. 什么是 Multi-Tool Agent（多工具智能体）。
2. 如何向大语言模型注册多个 Python 工具。
3. 如何让模型根据用户任务自主选择工具。
4. 如何使用 `tool_calls` 获取模型的工具调用请求。
5. 如何使用 Agent Loop 实现多轮工具调用。
6. 如何将工具执行结果反馈给模型，并生成最终回答。

## 📁 项目结构

```text
agent-from-scratch/
├── tutorials/
│   ├── 01_tool_calling/
│   └── 02_multi_tool_agent/
│       ├── main.py
│       └── README.md
└── requirements.txt
```

其中：

- `main.py`：多工具 Agent 的完整实现。
- `README.md`：本节课的学习教程。
- `requirements.txt`：项目依赖文件，位于仓库根目录。

## 🧠 核心原理

传统大语言模型主要负责生成文本，而 Agent 可以通过调用外部工具来完成具体任务。

本项目提供三个计算工具：

| 工具名称 | 功能 | 示例 |
|---|---|---|
| add | 加法计算 | add(10, 5) → 15 |
| subtract | 减法计算 | subtract(10, 5) → 5 |
| multiply | 乘法计算 | multiply(10, 5) → 50 |

当用户输入复杂计算任务时，大语言模型可以根据任务需要选择工具，并利用工具返回的结果继续计算。

### Agent 执行流程

```text
用户输入问题
     ↓
大语言模型分析任务
     ↓
判断是否需要调用工具
     ↓
   ┌──────────────┐
   │  是否需要工具  │
   └──────────────┘
      ↓        ↓
     是        否
      ↓        ↓
选择工具     输出答案
      ↓
执行 Python 函数
      ↓
返回工具结果
      ↓
再次请求大语言模型
      ↓
继续判断是否需要工具
```

这就是 Agent Loop（智能体执行循环）的基本思想。

需要注意：**大模型负责决策，Python 程序负责实际执行工具。**

## ⚙️ 环境配置

### 1. 安装 Python

建议使用 Python 3.10 或更高版本。

### 2. 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

确保 `requirements.txt` 中包含：

```text
openai
```

### 3. 配置 DeepSeek API Key

本项目使用 DeepSeek 的 OpenAI 兼容接口。

在 Windows PowerShell 中执行：

```powershell
$env:DEEPSEEK_API_KEY="your_api_key"
```

请将 `your_api_key` 替换为自己的 API Key。

注意：不要将真实 API Key 写入源代码或上传到 GitHub。

## 🚀 运行项目

在仓库根目录执行：

```bash
python tutorials/02_multi_tool_agent/main.py
```

然后输入：

```text
先计算12乘以8，再加上25，最后减去11。
```

预期计算过程：

```text
multiply(12, 8) = 96
add(96, 25) = 121
subtract(121, 11) = 110
```

最终结果：

```text
110
```

模型实际的工具调用轮数和输出文字可能有所不同，但正确计算结果应当一致。

## 🔍 核心代码解析

### 1. 注册工具

```python
TOOL_FUNCTIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply
}
```

这个字典将工具名称映射到对应的 Python 函数。

### 2. 获取模型的工具调用

```python
message = response.choices[0].message

if message.tool_calls:
    # 执行工具调用
    pass
```

`tool_calls` 包含模型请求调用的工具名称、参数和调用 ID。

### 3. 执行工具

```python
result = TOOL_FUNCTIONS[name](**arguments)
```

程序根据工具名称找到对应函数，并传入模型提供的参数。

### 4. 返回工具结果

```python
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": str(result)
})
```

通过 `tool_call_id`，模型可以将工具执行结果与之前的调用请求对应起来。

### 5. Agent Loop

```python
for round_num in range(max_rounds):
    # 请求模型
    # 检查工具调用
    # 执行工具
    # 返回结果
```

Agent 可以多轮调用工具，直到模型给出最终答案或达到最大执行轮数。

## 🧪 练习任务

完成项目后，尝试以下问题：

- 计算 15 × 6 + 20。
- 计算 (100 - 45) × 3。
- 计算 12 × 8 + 25 - 11。
- 尝试让模型计算一个需要多个步骤的复杂表达式。

进阶挑战：自行增加一个除法工具 `divide(a, b)`，并处理除数为零的情况。

## 📚 本节总结

本节课实现了一个基础的 Multi-Tool Agent。

它已经具备三个核心能力：

1. **工具选择**：根据任务选择相应工具。
2. **工具执行**：调用真实的 Python 函数。
3. **循环决策**：根据执行结果决定下一步操作。

但是，当前 Agent 仍存在一些局限，例如缺少复杂状态管理、持久化记忆和完善的异常处理机制。

后续将使用 LangGraph 等框架逐步解决这些问题。

## 🔜 下一课预告

**Lesson 03：使用 LangGraph 构建状态化 Agent**

下一课将学习：

- 什么是 State（状态）。
- 什么是 Node（节点）。
- 什么是 Edge（边）。
- 如何构建 Agent 的状态图。
- 如何使用条件边实现工具调用循环。

---

**Agent From Scratch — 从零开始构建 AI Agent**

Learning by Building · 从原理到实践
