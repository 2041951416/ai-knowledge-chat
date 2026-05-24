"""文档解析与智能分块"""
import re
from pathlib import Path
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def read_file(file_path: str) -> str | None:
    """读取多种格式文档"""
    path = Path(file_path)
    if not path.exists():
        return None
    suffix = path.suffix.lower()

    if suffix in (".txt", ".md"):
        return path.read_text("utf-8", errors="ignore")

    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            return None

    elif suffix in (".docx", ".doc"):
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            return None

    return None


def split_text(text: str, chunk_size: int = CHUNK_SIZE,
               chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """按段落+句子语义分块"""
    text = text.strip()
    if not text:
        return []

    # 按段落拆分
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 段落很短，累积
        if len(current) + len(para) < chunk_size:
            current += ("\n" + para) if current else para
            continue

        # 当前段落放不下了，保存当前块
        if current:
            chunks.append(current)
            # 重叠部分
            current = current[-chunk_overlap:] + "\n" + para if chunk_overlap > 0 else para
        elif len(para) > chunk_size:
            # 段落超长，按句子拆
            sentences = re.split(r'(?<=[。！？.!?\n])\s*', para)
            buf = ""
            for sent in sentences:
                if not sent.strip():
                    continue
                if len(buf) + len(sent) > chunk_size and buf:
                    chunks.append(buf)
                    buf = buf[-chunk_overlap:] + sent if chunk_overlap > 0 else sent
                else:
                    buf += sent
            if buf:
                chunks.append(buf)
            current = ""
        else:
            current = para

    if current:
        chunks.append(current)

    return chunks


def load_and_chunk(directory: str, single_file: str | None = None):
    """加载文档并分块

    如果指定 single_file，只处理单个文件
    否则处理目录下所有文件
    返回值: (chunks, metadata)
    """
    doc_dir = Path(directory)
    if not doc_dir.exists():
        return [], []

    files_to_process = []
    if single_file:
        fp = doc_dir / single_file
        if fp.exists():
            files_to_process = [fp]
    else:
        files_to_process = list(doc_dir.iterdir())

    all_chunks = []
    all_metadata = []

    for file_path in files_to_process:
        if not file_path.is_file():
            continue
        text = read_file(str(file_path))
        if not text or not text.strip():
            continue
        chunks = split_text(text)
        all_chunks.extend(chunks)
        all_metadata.extend([{
            "source": file_path.name,
            "type": file_path.suffix.lower().lstrip("."),
        } for _ in chunks])

    return all_chunks, all_metadata
