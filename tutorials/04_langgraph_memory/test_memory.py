"""Offline tests: verify memory isolation and SQLite restart, no DeepSeek key needed.

Run: python test_memory.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph, add_messages


class TestState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def build_test_graph(saver):
    def responder(state: TestState):
        count = sum(isinstance(m, HumanMessage) for m in state["messages"])
        return {"messages": [AIMessage(content=f"提问轮数：{count}")]}

    builder = StateGraph(TestState)
    builder.add_node("reply", responder)
    builder.add_edge(START, "reply")
    builder.add_edge("reply", END)
    return builder.compile(checkpointer=saver)


def send(graph, thread: str, message: str) -> str:
    config = {"configurable": {"thread_id": thread}}
    result = graph.invoke({"messages": [HumanMessage(content=message)]}, config)
    return result["messages"][-1].content


def main():
    with TemporaryDirectory() as folder:
        db_path = str(Path(folder) / "test_history.sqlite")
        with SqliteSaver.from_conn_string(db_path) as saver:
            graph = build_test_graph(saver)
            assert send(graph, "A", "第一问") == "提问轮数：1"
            assert send(graph, "A", "第二问") == "提问轮数：2"
            assert send(graph, "B", "独立新会话") == "提问轮数：1"
        # Close and reopen the database: thread A keeps its previous state.
        with SqliteSaver.from_conn_string(db_path) as saver:
            graph = build_test_graph(saver)
            assert send(graph, "A", "重启后的第三问") == "提问轮数：3"
            assert send(graph, "B", "第二问") == "提问轮数：2"
        print("全部测试通过：同会话记忆、不同会话隔离、SQLite 重启后持久化。")


if __name__ == "__main__":
    main()
