"""Streamlit 前端 - 带对话历史和文档管理"""
import streamlit as st
import requests
from pathlib import Path

API_BASE = "http://localhost:8001"

st.set_page_config(page_title="AI 知识库", page_icon="📚", layout="wide")
st.title("📚 AI 个人知识库")

# ─── 初始化 session 状态 ───
if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role":..., "content":..., "sources":...}]
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()  # 已上传的文件名集合


def chat_history() -> list[dict]:
    """转成 API 需要的格式"""
    result = []
    for m in st.session_state.messages:
        result.append({"role": m["role"], "content": m["content"]})
    return result


# ─── 侧边栏 ───
with st.sidebar:
    st.header("📄 文档管理")

    # 上传
    uploaded_file = st.file_uploader(
        "上传文档（TXT/PDF/DOCX/MD）", type=["txt", "pdf", "docx", "md"]
    )
    if uploaded_file is not None and uploaded_file.name not in st.session_state.uploaded_files:
        with st.status("正在上传并索引...", expanded=True) as status:
            try:
                resp = requests.post(
                    f"{API_BASE}/upload",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    timeout=120,
                )
                if resp.ok:
                    data = resp.json()
                    st.success(f"✅ {data['message']}")
                    st.session_state.uploaded_files.add(uploaded_file.name)
                else:
                    st.error(f"❌ 上传失败: {resp.text}")
            except requests.exceptions.ConnectionError:
                st.error("❌ 无法连接后端服务，请确认 API 已启动")
            except requests.exceptions.Timeout:
                st.error("❌ 上传超时，文件可能过大")

    # 操作按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重新索引", use_container_width=True):
            with st.spinner("正在重新索引..."):
                try:
                    resp = requests.post(f"{API_BASE}/reindex", timeout=120)
                    if resp.ok:
                        st.success(resp.json()["message"])
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
    with col2:
        if st.button("🗑️ 清空", use_container_width=True):
            try:
                resp = requests.post(f"{API_BASE}/clear", timeout=10)
                if resp.ok:
                    st.success("已清空")
                    st.session_state.messages = []
                    st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    # 来源文件列表
    st.divider()
    try:
        resp = requests.get(f"{API_BASE}/sources", timeout=5)
        if resp.ok:
            sources = resp.json()["sources"]
            if sources:
                st.caption(f"📁 已索引文件 ({len(sources)})")
                for s in sources:
                    st.markdown(f"- `{s}`")
            else:
                st.caption("📁 知识库为空，请上传文档")
    except Exception:
        st.caption("⚠️ 后端未连接")

    # 知识库统计
    try:
        resp = requests.get(f"{API_BASE}/stats", timeout=5)
        if resp.ok:
            st.caption(f"📊 文档块数：**{resp.json()['doc_count']}**")
    except Exception:
        pass

    st.divider()
    st.caption("💡 上传文档后即可提问\n支持 TXT/PDF/DOCX/MD")

    # 清空对话
    if st.button("💬 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ─── 主区域：聊天 ───

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 来源"):
                for s in msg["sources"]:
                    st.write(f"- `{s}`")

# 输入框
if prompt := st.chat_input("输入你的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用后端
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ 思考中...")
        try:
            resp = requests.post(
                f"{API_BASE}/chat",
                json={
                    "query": prompt,
                    "use_rag": True,
                    "history": chat_history()[:-1],  # 排除当前提问
                },
                timeout=90,
            )
            if resp.ok:
                data = resp.json()
                answer = data["answer"]
                sources = data.get("sources", [])
                note = data.get("note", "")
                display = answer
                if note:
                    display += f"\n\n> 💡 *{note}*"
                placeholder.markdown(display)
                if sources:
                    with st.expander("📎 来源"):
                        for s in sources:
                            st.write(f"- `{s}`")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })
            else:
                placeholder.error(f"❌ 请求失败: {resp.status_code} {resp.text}")
        except requests.exceptions.ConnectionError:
            placeholder.error("❌ 无法连接后端，请确认 API 服务已启动")
        except requests.exceptions.Timeout:
            placeholder.error("❌ 请求超时，请重试")
