"""Lesson 04: LangGraph checkpoint memory (DeepSeek + tools + SQLite).

Run:
    python main.py
    python main.py --storage memory
    python main.py --thread demo-2
"""

import argparse
import os
import re
from contextlib import nullcontext
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "chat_history.sqlite"
SYSTEM_PROMPT = (
    "你是一个严谨的中文计算助手。涉及加、减、乘法时，请调用工具而不是心算。"
    "如果用户使用'刚才的结果''再加'等说法，应结合当前会话的历史消息理解。"
    "不同会话之间不得擅自共享信息。回答清楚、简洁。"
)


@tool
def add(a: float, b: float) -> float:
    """计算 a 加 b 的结果。"""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """计算 a 减 b 的结果。"""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """计算 a 乘 b 的结果。"""
    return a * b


TOOLS = [add, subtract, multiply]


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    llm_calls: int


def build_agent(checkpointer):
    """Compared with Lesson 03: compile the graph with a checkpointer."""
    load_dotenv(dotenv_path=PROJECT_DIR / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key == "your_deepseek_api_key_here":
        raise ValueError("未配置 DEEPSEEK_API_KEY，请在本地创建并填写 .env。")

    model = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        api_key=api_key,
        base_url="https://api.deepseek.com",
    ).bind_tools(TOOLS)

    def call_model(state: AgentState):
        response = model.invoke(
            [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        )
        return {
            "messages": [response],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    def route_after_model(state: AgentState) -> Literal["tools", "end"]:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return "end"

    builder = StateGraph(AgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent", route_after_model, {"tools": "tools", "end": END}
    )
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


def thread_config(thread_id: str) -> dict:
    # The thread_id is the primary key for the saved conversation state.
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}


def run_question(agent, thread_id: str, question: str) -> None:
    config = thread_config(thread_id)
    answer = ""
    try:
        # Only this turn's NEW message is passed in. Checkpointer restores history.
        updates = agent.stream(
            {"messages": [HumanMessage(content=question)]},
            config=config,
            stream_mode="updates",
        )
        for update in updates:
            for node, changes in update.items():
                if node == "tools":
                    for message in changes.get("messages", []):
                        if isinstance(message, ToolMessage):
                            print(f"    [工具 {message.name}] {message.content}")
                elif node == "agent":
                    for message in changes.get("messages", []):
                        if isinstance(message, AIMessage):
                            if message.tool_calls:
                                names = ", ".join(call["name"] for call in message.tool_calls)
                                print(f"    [调用工具] {names}")
                            else:
                                answer = str(message.content)
        print(f"Agent：{answer or '（模型未返回可显示的文本）'}")
    except GraphRecursionError:
        print("执行已终止：超过最大执行步数，请检查工具循环。")
    except Exception as exc:
        print(f"本轮执行失败：{type(exc).__name__}: {exc}")


def show_history(agent, thread_id: str) -> None:
    snapshot = agent.get_state(thread_config(thread_id))
    messages = snapshot.values.get("messages", [])
    visible = []
    for message in messages:
        if isinstance(message, HumanMessage):
            visible.append(("你", str(message.content)))
        elif isinstance(message, AIMessage) and not message.tool_calls and message.content:
            visible.append(("Agent", str(message.content)))
    if not visible:
        print("当前会话还没有历史消息。")
        return
    print(f"\n会话 {thread_id} 的最近 12 条对话消息：")
    for role, content in visible[-12:]:
        preview = content.replace("\n", " ")
        print(f"  {role}：{preview[:200]}{'…' if len(preview) > 200 else ''}")


def valid_thread_id(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph Lesson 04: checkpoint memory")
    parser.add_argument("--storage", choices=["sqlite", "memory"], default="sqlite")
    parser.add_argument("--thread", default="demo-1", help="会话 ID，如 demo-1")
    args = parser.parse_args()

    if not valid_thread_id(args.thread):
        parser.error("--thread 只能由字母、数字、下划线、连字符组成，长度为 1-64")

    # SQLite persists after restart; InMemorySaver lasts only for this process.
    manager = (
        SqliteSaver.from_conn_string(str(DATABASE_PATH))
        if args.storage == "sqlite"
        else nullcontext(InMemorySaver())
    )
    with manager as checkpointer:
        try:
            agent = build_agent(checkpointer)
        except ValueError as exc:
            print(exc)
            return

        thread_id = args.thread
        print("Lesson 04 | LangGraph 对话记忆 Agent")
        print(f"存储：{args.storage} | 当前会话：{thread_id}")
        if args.storage == "sqlite":
            print(f"数据库：{DATABASE_PATH}")
        print("命令：/history 查看历史；/thread 会话ID 切换会话；/state 查看状态；q 退出。")

        while True:
            try:
                line = input(f"\n你 ({thread_id})：").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n再见。")
                break
            if not line:
                continue
            if line.lower() in {"q", "quit", "exit", "/exit"}:
                print("再见。")
                break
            if line == "/history":
                show_history(agent, thread_id)
                continue
            if line == "/state":
                snapshot = agent.get_state(thread_config(thread_id))
                state = snapshot.values
                print(
                    f"会话：{thread_id} | 消息数：{len(state.get('messages', []))} "
                    f"| 累计大模型调用次数：{state.get('llm_calls', 0)}"
                )
                continue
            if line.startswith("/thread"):
                parts = line.split()
                if len(parts) != 2 or not valid_thread_id(parts[1]):
                    print("用法：/thread demo-2（会话 ID 仅允许字母、数字、下划线和连字符）")
                    continue
                thread_id = parts[1]
                print(f"已切换到会话：{thread_id}")
                continue
            run_question(agent, thread_id, line)


if __name__ == "__main__":
    main()
