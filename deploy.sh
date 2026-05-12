#!/bin/bash
# credit-web 一键部署脚本（v2.0 车辆版）
# 用法: ./deploy.sh <服务器IP> [用户名] [--reset-db]
# 示例: ./deploy.sh 123.123.123.123 root
#       ./deploy.sh 123.123.123.123 root --reset-db
set -e

if [ -z "$1" ]; then
    echo "用法: ./deploy.sh <服务器IP> [用户名] [--reset-db]"
    echo "  --reset-db  强制重建数据库（首次部署或结构变更时使用）"
    exit 1
fi

SERVER_IP="$1"
USER="${2:-root}"
RESET_DB=false
if [ "${3:-}" = "--reset-db" ]; then RESET_DB=true; fi

PROJECT="credit-web"
TARBALL="${PROJECT}-deploy.tar.gz"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. 本地构建前端（服务器跳过 Node 构建，省内存）
echo "=== [1/5] 本地构建前端 ==="
cd "$SCRIPT_DIR/frontend"
npm run build 2>&1 | tail -3
echo "  前端构建完成 → dist/"

# 2. 打包项目（含前端产物 dist/）
echo "=== [2/5] 打包项目 ==="
cd "$SCRIPT_DIR/.."
tar --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.db' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    -czf "/tmp/${TARBALL}" "$PROJECT"
echo "  打包完成: /tmp/${TARBALL}"

# 3. 上传
echo "=== [3/5] 上传到 ${USER}@${SERVER_IP} ==="
scp "/tmp/${TARBALL}" "${USER}@${SERVER_IP}:/root/"

# 4. 远程部署
echo "=== [4/5] 远程部署 ==="

if $RESET_DB; then
    RESET_CMD="docker compose down -v"
else
    RESET_CMD="docker compose down"
fi

ssh "${USER}@${SERVER_IP}" << SSH_CMD
set -e
cd /root

echo "停止旧容器..."
cd credit-web 2>/dev/null && ${RESET_CMD} 2>/dev/null || true
cd /root

echo "解压新版本..."
rm -rf /root/credit-web
tar xzf credit-web-deploy.tar.gz
cd credit-web

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

echo "构建镜像并启动..."
docker compose build
docker compose up -d

echo ""
echo "=== 部署完成 ==="
echo "访问: http://${SERVER_IP}"
SSH_CMD

# 5. 清理
echo "=== [5/5] 清理 ==="
rm -f "/tmp/${TARBALL}"
echo "完成！"
