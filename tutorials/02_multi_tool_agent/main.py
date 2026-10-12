import os
import json
from openai import OpenAI

# 1. 初始化大模型客户端
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

MODEL = "deepseek-flash"


# 2. 定义三个 Python 工具
def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


# 3. 注册允许 Agent 使用的工具
TOOL_FUNCTIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
}

def make_tool(name, description):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
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


TOOLS = [
    make_tool("add", "计算两个数字之和"),
    make_tool("subtract", "计算两个数字之差：a-b"),
    make_tool("multiply", "计算两个数字之积"),
]


# 4. Agent 主循环
def run_agent(question, max_rounds=5):
    messages = [
        {
            "role": "system",
            "content": (
                "你是数学计算助手。"
                "涉及运算时必须使用提供的工具。"
                "复杂计算应分步执行。"
            )
        },
        {"role": "user", "content": question}
    ]

    for round_num in range(max_rounds):
        print(f"\n第 {round_num + 1} 轮")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        # 如果不需要工具，返回最终答案
        if not message.tool_calls:
            return message.content or "模型未返回答案"

        # 处理当前轮的所有工具调用
        for tool_call in message.tool_calls:
            name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )

                if name not in TOOL_FUNCTIONS:
                    raise ValueError(f"未知工具: {name}")

                result = TOOL_FUNCTIONS[name](
                    **arguments
                )
                print(f"调用 {name}: {arguments}")
                print(f"结果: {result}")

                tool_result = str(result)

            except (ValueError, TypeError, KeyError) as e:
                tool_result = f"工具执行失败: {e}"

            # 将结果返回给大模型
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result
            })

    return "已达到最大执行轮数，任务尚未完成。"


if __name__ == "__main__":
    question = input("请输入你的问题：")
    answer = run_agent(question)
    print("\n最终回答：", answer)
