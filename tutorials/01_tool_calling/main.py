import json
import os
from openai import OpenAI

# 读取环境变量中的 API Key
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# 定义第一个 Python 工具
def multiply(a: float, b: float) -> float:
    return a * b


# 将工具描述提供给大模型
tools = [
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "计算两个数字的乘积",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        }
    }
]


def run_agent(question: str):
    messages = [
        {"role": "system", "content": "你是一个善于使用工具的AI助手。"},
        {"role": "user", "content": question}
    ]

    # 限制最多执行5轮，避免无限循环
    for _ in range(5):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        # 模型不再要求调用工具，直接返回答案
        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if name == "multiply":
                result = multiply(args["a"], args["b"])
            else:
                result = "Unknown tool"

            print(f"[Tool] {name}: {args} -> {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

    return "已达到最大工具调用轮数"


if __name__ == "__main__":
    print("AI Agent 已启动，输入 exit 退出")

    while True:
        question = input("\n你：").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        try:
            answer = run_agent(question)
            print(f"Agent：{answer}")
        except Exception as e:
            print(f"运行出错：{e}")
