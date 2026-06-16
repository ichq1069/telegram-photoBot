#!/bin/bash
set -e

echo "=== Telegram PhotoBot Manager - 本地开发启动 ==="

echo "[1/2] 启动后端服务..."
cd "$(dirname "$0")/backend"
pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
mkdir -p /tmp/photobot_data/{uploads,thumbnails,logs}
export SQLITE_PATH=/tmp/photobot_data/photobot.db
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[2/2] 启动前端服务..."
cd "$(dirname "$0")/frontend"
npm install
npm run dev &
FRONTEND_PID=$!

echo ""
echo "后端: http://localhost:8000"
echo "前端: http://localhost:5173"
echo "默认账号: admin / admin123"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
