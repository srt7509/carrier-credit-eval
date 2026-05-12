#!/bin/bash

# 延长物流信用评价系统 - 一键启动
# Flask 后端（端口5001）同时服务前端静态文件 + API

echo "======================================"
echo "  延长物流信用评价系统 - 一键启动"
echo "======================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 1. 构建前端
echo "[1/2] 构建前端..."
cd "$FRONTEND_DIR"
npm run build > "$PROJECT_DIR/build.log" 2>&1
if [ $? -ne 0 ]; then
    echo "前端构建失败，请查看 build.log"
    exit 1
fi
echo "  前端构建完成 → $FRONTEND_DIR/dist/"

# 2. 启动 Flask 后端（端口 5001，服务前端 + API）
echo "[2/2] 启动后端服务..."
cd "$BACKEND_DIR"
pixi run python app.py > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

sleep 2
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "后端启动失败，请查看 backend.log"
    exit 1
fi

echo ""
echo "======================================"
echo "  服务已启动！"
echo "======================================"
echo ""
echo "  访问地址：http://localhost:5001"
echo ""
echo "  日志文件："
echo "    构建日志：$PROJECT_DIR/build.log"
echo "    后端日志：$PROJECT_DIR/backend.log"
echo ""
echo "  停止服务：./stop.sh 或按 Ctrl+C"
echo "======================================"

trap "echo ''; echo '停止服务...'; kill $BACKEND_PID 2>/dev/null; echo '已停止'; exit 0" INT TERM
wait
