"""FastAPI 路由"""
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from backend.rag_pipeline import ask_rag, ask_direct
from backend.document_loader import load_and_chunk
from backend.embedding_store import get_store

app = FastAPI(title="AI 知识库 API")


class ChatRequest(BaseModel):
    query: str
    use_rag: bool = True
    history: list[dict] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


@app.get("/health")
async def health():
    return {"status": "ok", "doc_count": get_store().count()}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.use_rag:
        result = await ask_rag(req.query, history=req.history or None)
        return ChatResponse(answer=result["answer"], sources=result["sources"])
    else:
        answer = await ask_direct(req.query, history=req.history or None)
        return ChatResponse(answer=answer)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文档并增量索引（不清空已有）"""
    save_dir = Path("./data/documents")
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)

    # 只索引新文件（不清空）
    text = load_and_chunk(str(save_dir), single_file=file.filename)
    if text is None:
        return {"message": f"无法解析文件 {file.filename}，请使用 TXT/PDF/DOCX/MD 格式"}

    chunks, metadata = text
    store = get_store()
    count = store.add_documents(chunks, metadata)

    return {
        "message": f"文件 {file.filename} 已上传并索引",
        "chunks": count,
        "total_docs": store.count(),
    }


@app.post("/reindex")
async def reindex():
    """清空并重新索引所有文档"""
    chunks, metadata = load_and_chunk("./data/documents")
    store = get_store()
    store.clear()
    count = store.add_documents(chunks, metadata)
    return {"message": "重新索引完成", "chunks": count, "total_docs": store.count()}


@app.get("/stats")
async def stats():
    return {"doc_count": get_store().count()}


@app.get("/sources")
async def list_sources():
    """获取所有来源文件列表"""
    return {"sources": get_store().get_all_sources()}


@app.post("/clear")
async def clear_knowledge():
    get_store().clear()
    return {"message": "知识库已清空"}
