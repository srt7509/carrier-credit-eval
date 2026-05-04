#!/bin/bash

# 信用评价系统一键启动脚本
# 同时启动后端（Flask）和前端（Vue预览服务器）

echo "======================================"
echo "  信用评价系统 - 一键启动"
echo "======================================"
echo ""

# 获取脚本所在目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 启动后端服务
echo "启动后端服务（Flask，端口5001）..."
cd "$BACKEND_DIR"
python app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端PID: $BACKEND_PID"

# 等待后端启动（2秒）
echo "等待后端启动..."
sleep 2

# 启动前端服务
echo "启动前端服务（Vite Preview）..."
cd "$FRONTEND_DIR"
npm run start > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"

# 等待前端构建和启动（5秒）
echo "等待前端构建和启动..."
sleep 5

echo ""
echo "======================================"
echo "  服务已启动！"
echo "======================================"
echo ""
echo "访问地址："
echo "  前端：http://localhost:4173 或 http://localhost:4174"
echo "  后端：http://localhost:5001"
echo ""
echo "日志文件："
echo "  后端日志：$BACKEND_DIR/backend.log"
echo "  前端日志：$FRONTEND_DIR/frontend.log"
echo ""
echo "停止服务："
echo "  按 Ctrl+C 停止所有服务"
echo "  或运行：./stop.sh"
echo ""
echo "======================================"

# 捕获Ctrl+C信号，停止所有服务
trap "echo ''; echo '停止所有服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '服务已停止'; exit 0" INT TERM

# 保持脚本运行，等待用户按Ctrl+C
wait
