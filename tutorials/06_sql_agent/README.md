# 第六课：SQL Agent

> 目标：让 Agent 能理解自然语言问题，并为 SQLite 数据库生成 SQL 查询。

本课先完成 SQL Agent 的基础设施，不急着一次性把所有功能做完。

## 本节学习目标

1. 使用 SQLite 保存结构化数据
2. 用 Python 初始化数据库
3. 获取数据库 Schema
4. 为后续 SQL Agent 准备数据库工具
5. 理解“自然语言 → SQL → 数据库 → 结果”的基本链路

## 项目结构

```text
06_sql_agent/
├── README.md
├── main.py
├── database.py
├── init_db.py
└── .gitignore
```

运行 `init_db.py` 后会自动生成：

```text
06_sql_agent/data/sales.db
```

数据库文件是本地生成文件，**不上传到 GitHub**。

## 第一步：初始化数据库

在仓库根目录执行：

```bash
python tutorials/06_sql_agent/init_db.py
```

看到：

```text
数据库初始化完成
```

即可。

## 第二步：查看数据库信息

执行：

```bash
python tutorials/06_sql_agent/main.py
```

程序会读取 SQLite 数据库，并输出表结构与示例数据。

## 本课核心流程

```text
用户自然语言问题
        ↓
      Agent
        ↓
读取数据库 Schema
        ↓
      生成 SQL
        ↓
   SQLite 执行查询
        ↓
     返回结果
        ↓
   Agent 组织答案
```

后续会继续把这个基础版本升级成真正的 SQL Agent，并加入 LLM SQL 生成、SQL 工具调用、安全只读查询、错误 SQL 自动修正和多轮自然语言查询。
