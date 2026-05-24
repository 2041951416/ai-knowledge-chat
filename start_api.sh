#! /bin/bash
# 启动后端 API（终端 1）
cd "$(dirname "$0")"
echo "📦 启动后端 API 服务..."
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
