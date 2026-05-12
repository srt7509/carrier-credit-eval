#!/bin/bash

# 延长物流信用评价系统 - 停止脚本

echo "======================================"
echo "  延长物流信用评价系统 - 停止服务"
echo "======================================"
echo ""

# 停止后端（端口 5001）
BACKEND_PID=$(lsof -ti:5001 2>/dev/null)
if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null
    sleep 1
    # 未响应则强制杀
    kill -9 $BACKEND_PID 2>/dev/null
    echo "后端服务已停止 (端口 5001)"
else
    echo "后端服务未运行 (端口 5001)"
fi

# 清理 Vite 开发服务器（端口 5173，如果使用 npm run dev）
DEV_PID=$(lsof -ti:5173 2>/dev/null)
if [ -n "$DEV_PID" ]; then
    kill -9 $DEV_PID 2>/dev/null
    echo "Vite 开发服务器已停止 (端口 5173)"
fi

# 清理残留 vite preview（端口 4173/4174，旧脚本遗留）
for port in 4173 4174; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$PID" ]; then
        kill -9 $PID 2>/dev/null
        echo "残留 preview 进程已停止 (端口 $port)"
    fi
done

echo ""
echo "======================================"
echo "  所有服务已停止"
echo "======================================"
