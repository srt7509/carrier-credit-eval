#!/bin/bash
# credit-web 一键部署脚本
# 用法: ./deploy.sh <服务器IP> [用户]
set -e

if [ -z "$1" ]; then
    echo "用法: ./deploy.sh <服务器IP> [用户名]"
    echo "示例: ./deploy.sh 123.123.123.123 root"
    exit 1
fi

SERVER_IP="$1"
USER="${2:-root}"
PROJECT="credit-web"
TARBALL="${PROJECT}-deploy.tar.gz"

# 1. 打包项目（排除不需要的文件）
echo "=== 打包项目 ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(basename "$SCRIPT_DIR")"
cd "$PARENT_DIR"
tar --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    -czf "/tmp/${TARBALL}" "${PROJECT_DIR}"

# 2. 上传到服务器
echo "=== 上传到 ${USER}@${SERVER_IP} ==="
scp "/tmp/${TARBALL}" "${USER}@${SERVER_IP}:/root/"

# 3. 远程部署
echo "=== 在服务器上部署 ==="
ssh "${USER}@${SERVER_IP}" << 'SSH_CMD'
set -e
cd /root
rm -rf /root/credit-web
tar xzf credit-web-deploy.tar.gz
cd credit-web

# 安装 Docker（如果没有的话）
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    apt-get update && apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker && systemctl start docker
fi

# 构建并启动
echo "构建并启动服务..."
docker compose build
docker compose up -d

echo ""
echo "=== 部署完成！==="
echo "访问地址: http://$(curl -s ifconfig.me)"
echo ""
SSH_CMD

# 清理
rm -f "/tmp/${TARBALL}"
echo "=== 本地临时文件已清理 ==="
