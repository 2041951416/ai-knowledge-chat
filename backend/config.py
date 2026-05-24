import os

# DeepSeek 配置（从环境变量读取，不要硬编码密钥）
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
