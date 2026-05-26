"""RAG 核心流水线：语义检索 + 带历史对话的生成"""
import httpx
from backend.config import (
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, TOP_K_RESULTS, MAX_HISTORY_ROUNDS
)
from backend.embedding_store import get_store


def build_context(docs: list[dict]) -> str:
    """将检索结果拼成上下文"""
    sections = []
    for i, d in enumerate(docs, 1):
        source = d["metadata"].get("source", "未知来源")
        sections.append(f"[{i}] 来源: {source}\n{d['content']}")
    return "\n\n".join(sections)


def build_messages(query: str, context: str, history: list[dict] | None):
    """构建带历史和上下文的 messages"""
    system = f"""你是一个知识库问答助手。请基于以下参考资料回答用户的问题。

注意事项：
- 如果参考资料足以回答问题，用中文给出清晰、详细的回答
- 如果参考资料不足以回答问题，请说"资料中没有相关答案"，不要编造
- 回答时适当引用资料中的具体内容
- 保持回答简洁有条理

参考资料：
{context}"""

    messages = [{"role": "system", "content": system}]

    # 添加历史对话（只保留最近 N 轮）
    if history:
        for msg in history[-MAX_HISTORY_ROUNDS * 2:]:
            messages.append(msg)

    messages.append({"role": "user", "content": query})
    return messages


async def ask_rag(query: str, history: list[dict] | None = None) -> dict:
    """RAG 全流程：语义检索 → 构建 prompt → 调用 LLM → 返回结果"""
    store = get_store()

    if store.count() == 0:
        # 知识库为空 → 回退到直接对话
        answer = await ask_direct(query, history)
        return {"answer": answer, "sources": []}

    # 1. 语义检索
    docs = store.search(query, top_k=TOP_K_RESULTS)

    # 2. 判断是否需要 RAG（相似度 > 0 表示至少有一定相关性）
    has_relevant = any(d["score"] > 0.15 for d in docs)

    if not has_relevant:
        # 没有相关内容 → 回退到直接对话
        answer = await ask_direct(query, history)
        return {
            "answer": answer,
            "sources": [],
            "note": "未在知识库中找到相关内容，以上为模型自身回答",
        }

    # 3. 构建上下文
    context = build_context(docs)

    # 4. 构建带历史的 messages
    messages = build_messages(query, context, history)

    # 5. 调用 LLM
    answer = await call_llm(messages)

    # 6. 提取来源
    sources = list(set(
        d["metadata"].get("source", "未知来源")
        for d in docs if d.get("metadata")
    ))

    return {"answer": answer, "sources": sources}


async def call_llm(messages: list[dict]) -> str:
    """调用 DeepSeek API"""
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def ask_direct(query: str, history: list[dict] | None = None) -> str:
    """直接对话（不检索知识库）"""
    messages = [{"role": "system", "content": "你是一个有用的AI助手。保持回答简洁准确。"}]
    if history:
        for msg in history[-MAX_HISTORY_ROUNDS * 2:]:
            messages.append(msg)
    messages.append({"role": "user", "content": query})
    return await call_llm(messages)
