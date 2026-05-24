#! /bin/bash
# 启动 Streamlit 前端（终端 2）
cd "$(dirname "$0")"
echo "🎨 启动 Streamlit 前端..."
streamlit run frontend.py --server.port 8501
