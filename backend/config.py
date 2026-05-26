import os
from pathlib import Path
from dotenv import load_dotenv

# 从 .env 文件加载环境变量（.env 不提交到 Git）
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(str(env_path))

# 然后从系统环境变量读取（set DEEPSEEK_API_KEY=xxx）
# 双重保障：.env 文件优先，系统环境变量次之
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = "deepseek-chat"

# 向量库持久化路径
CHROMA_DB_PATH = "./data/chroma_db"

# RAG 参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5            # 检索返回的文档块数

# 对话历史最大轮数
MAX_HISTORY_ROUNDS = 6
