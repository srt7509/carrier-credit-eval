#!/bin/bash

# 信用评价系统停止脚本
# 停止所有运行中的服务

echo "======================================"
echo "  信用评价系统 - 停止服务"
echo "======================================"
echo ""

# 停止后端服务（端口5001）
echo "停止后端服务（端口5001）..."
BACKEND_PID=$(lsof -ti:5001)
if [ -n "$BACKEND_PID" ]; then
    kill -9 $BACKEND_PID 2>/dev/null
    echo "后端服务已停止 (PID: $BACKEND_PID)"
else
    echo "后端服务未运行"
fi

# 停止前端服务（端口4173）
echo "停止前端服务（端口4173）..."
FRONTEND_PID1=$(lsof -ti:4173)
if [ -n "$FRONTEND_PID1" ]; then
    kill -9 $FRONTEND_PID1 2>/dev/null
    echo "前端服务已停止 (PID: $FRONTEND_PID1)"
else
    echo "前端服务（4173）未运行"
fi

# 停止前端服务（端口4174）
echo "停止前端服务（端口4174）..."
FRONTEND_PID2=$(lsof -ti:4174)
if [ -n "$FRONTEND_PID2" ]; then
    kill -9 $FRONTEND_PID2 2>/dev/null
    echo "前端服务已停止 (PID: $FRONTEND_PID2)"
else
    echo "前端服务（4174）未运行"
fi

echo ""
echo "======================================"
echo "  所有服务已停止"
echo "======================================"
