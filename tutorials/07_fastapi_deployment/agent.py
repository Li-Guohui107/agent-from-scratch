import os

from dotenv import load_dotenv

load_dotenv()


def run_agent(message: str) -> tuple[str, str]:
    """无 API Key 时返回本地演示结果；配置 Key 后调用 DeepSeek。"""
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return (
            "（本地演示模式）我收到了你的问题："
            f"{message}\n配置 DEEPSEEK_API_KEY 后，即可切换到真实大模型回答。",
            "demo",
        )

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=30.0,
            max_retries=1,
        )
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "你是一个简洁、可靠的中文 AI 助手。请清晰回答用户问题。"},
                {"role": "user", "content": message},
            ],
            temperature=0.2,
        )
        reply = response.choices[0].message.content or "模型没有返回文本内容。"
        return reply, "deepseek"
    except Exception as exc:
        # 不向客户端暴露原始异常，避免泄露供应商响应、配置等内部细节。
        raise RuntimeError("调用大模型接口失败，请检查 API Key、网络和模型配置。") from exc
