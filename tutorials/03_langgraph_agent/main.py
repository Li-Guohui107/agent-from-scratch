"""Lesson 03: use LangGraph to orchestrate a multi-tool DeepSeek Agent."""

import os
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import ToolNode


@tool
def add(a: float, b: float) -> float:
    """计算两个数相加的结果。"""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """计算 a 减去 b 的结果。"""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """计算两个数相乘的结果。"""
    return a * b


TOOLS = [add, subtract, multiply]
SYSTEM_PROMPT = (
    "你是一名严谨的计算助手。涉及加法、减法或乘法时，应调用相应工具，"
    "不要心算。多步骤计算时，先获取工具结果，再继续调用工具，最后用中文回答。"
)


class AgentState(TypedDict):
    # add_messages 把新消息追加/合并到历史消息，而不是直接覆盖。
    messages: Annotated[list[BaseMessage], add_messages]
    llm_calls: int


def build_agent():
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未设置 DEEPSEEK_API_KEY。请参考 .env.example 创建 .env 文件。")

    model = ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    model_with_tools = model.bind_tools(TOOLS)

    def call_model(state: AgentState) -> dict:
        """Agent 节点：根据当前状态决定是否调用工具。"""
        response = model_with_tools.invoke(
            [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        )
        return {
            "messages": [response],
            "llm_calls": state["llm_calls"] + 1,
        }

    def route_after_model(state: AgentState) -> Literal["tools", "end"]:
        """条件边：模型请求工具就前往 tools，否则结束。"""
        last_message = state["messages"][-1]
        return "tools" if isinstance(last_message, AIMessage) and last_message.tool_calls else "end"

    builder = StateGraph(AgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        route_after_model,
        {"tools": "tools", "end": END},
    )
    builder.add_edge("tools", "agent")
    return builder.compile()


def run_question(agent, question: str) -> None:
    print(f"\n用户：{question}")
    try:
        # updates 模式展示每一个节点的增量输出，有助于观察执行流程。
        for update in agent.stream(
            {"messages": [HumanMessage(content=question)], "llm_calls": 0},
            config={"recursion_limit": 20},
            stream_mode="updates",
        ):
            for node_name, changes in update.items():
                print(f"[进入节点] {node_name}")
                for message in changes.get("messages", []):
                    if isinstance(message, AIMessage):
                        if message.tool_calls:
                            for tool_call in message.tool_calls:
                                print(f"  [工具请求] {tool_call['name']}({tool_call['args']})")
                        elif message.content:
                            print(f"  [最终回答] {message.content}")
                    elif isinstance(message, ToolMessage):
                        print(f"  [工具结果] {message.name}: {message.content}")
                if "llm_calls" in changes:
                    print(f"  [模型调用次数] {changes['llm_calls']}")
    except GraphRecursionError:
        print("[执行终止] 超过最大图执行步数，请检查是否持续重复调用工具。")


def main() -> None:
    agent = build_agent()
    print("Lesson 03 | LangGraph 多工具 Agent")
    print("输入问题，例如：先计算 12 + 8，再把结果乘以 3。输入 q 退出。")
    while True:
        question = input("\n你：").strip()
        if question.lower() in {"q", "quit", "exit"}:
            break
        if question:
            run_question(agent, question)


if __name__ == "__main__":
    main()
