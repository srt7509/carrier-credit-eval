#!/bin/bash
# credit-web 一键部署脚本（v2.0 车辆版）
# 用法: ./deploy.sh <服务器IP> [用户名] [--reset-db]
# 示例: ./deploy.sh 123.123.123.123 root
#       ./deploy.sh 123.123.123.123 root --reset-db   # 重置数据库
set -e

if [ -z "$1" ]; then
    echo "用法: ./deploy.sh <服务器IP> [用户名] [--reset-db]"
    echo "示例: ./deploy.sh 123.123.123.123 root"
    echo "      ./deploy.sh 123.123.123.123 root --reset-db   # 强制重建数据库"
    exit 1
fi

SERVER_IP="$1"
USER="${2:-root}"
RESET_DB=false
if [ "${3:-}" = "--reset-db" ]; then
    RESET_DB=true
fi

PROJECT="credit-web"
TARBALL="${PROJECT}-deploy.tar.gz"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(basename "$SCRIPT_DIR")"

# 1. 打包项目
echo "=== [1/4] 打包项目 ==="
cd "$PARENT_DIR"
tar --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='dist' \
    --exclude='.DS_Store' \
    -czf "/tmp/${TARBALL}" "${PROJECT_DIR}"
echo "  打包完成: /tmp/${TARBALL}"

# 2. 上传到服务器
echo "=== [2/4] 上传到 ${USER}@${SERVER_IP} ==="
scp "/tmp/${TARBALL}" "${USER}@${SERVER_IP}:/root/"
echo "  上传完成"

# 3. 远程停止旧容器、解压、重建、启动
echo "=== [3/4] 远程部署 ==="

if $RESET_DB; then
    RESET_CMD="docker compose down -v"
else
    RESET_CMD="docker compose down"
fi

ssh "${USER}@${SERVER_IP}" << SSH_CMD
set -e
cd /root

# 停止旧容器
echo "停止旧容器..."
cd credit-web 2>/dev/null && ${RESET_CMD} 2>/dev/null || true
cd /root

# 解压新版本
echo "解压新版本..."
rm -rf /root/credit-web
tar xzf credit-web-deploy.tar.gz
cd credit-web

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    apt-get update && apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \$(. /etc/os-release && echo "\$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker && systemctl start docker
fi

# 构建并启动
echo "构建镜像并启动..."
docker compose build --no-cache
docker compose up -d

echo ""
echo "=== 部署完成 ==="
echo "访问地址: http://${SERVER_IP}"
echo ""
echo "查看日志: docker compose logs -f"
echo "重置数据: 在服务器上运行: docker compose down -v && docker compose up -d"
SSH_CMD

# 4. 清理
echo "=== [4/4] 清理本地临时文件 ==="
rm -f "/tmp/${TARBALL}"
echo "完成！"
