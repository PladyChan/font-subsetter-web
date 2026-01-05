#!/usr/bin/env bash
set -e

# 一键本地启动脚本
# 支持自定义变量：
#   PYTHON               指定 Python 可执行文件（默认 python3）
#   PIP_INDEX_URL        指定 PyPI 镜像（默认清华）
#   PIP_EXTRA_INDEX_URL  额外镜像
#   HOST                 监听地址（默认 127.0.0.1）
#   PORT                 监听端口（默认 8888）
#   FLASK_APP            Flask 入口文件（默认 app.py）
#   FLASK_ENV            Flask 环境（默认 production）

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# 检查 Python 是否安装
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "[ERROR] 未找到 Python 3，请先安装 Python 3"
    echo "[ERROR] 下载地址: https://www.python.org/downloads/"
    exit 1
fi

# 检查 Python 版本
PYTHON_VERSION=$("$PYTHON" --version 2>&1 | awk '{print $2}')
echo "[INFO] 检测到 Python 版本: $PYTHON_VERSION"

VENV="$ROOT/.venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[INFO] 创建虚拟环境 $VENV"
  "$PYTHON" -m venv "$VENV"
fi

source "$VENV/bin/activate"

PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-}"

# 确保虚拟环境中有 pip，并始终使用 venv 里的 pip
PIP_CMD="$VENV/bin/pip"
if [ ! -x "$PIP_CMD" ]; then
  echo "[INFO] 虚拟环境中未找到 pip，正在安装..."
  "$VENV/bin/python" -m ensurepip --upgrade
  PIP_CMD="$VENV/bin/pip"
fi

# 检查 requirements.txt 是否存在
if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] 未找到 requirements.txt 文件"
    exit 1
fi

echo "[INFO] 升级 pip"
"$PIP_CMD" install --upgrade pip >/dev/null 2>&1 || {
    echo "[WARN] pip 升级失败，继续尝试安装依赖..."
}

echo "[INFO] 安装依赖（镜像：$PIP_INDEX_URL）"
if [ -n "$PIP_EXTRA_INDEX_URL" ]; then
  "$PIP_CMD" install -r requirements.txt -i "$PIP_INDEX_URL" --extra-index-url "$PIP_EXTRA_INDEX_URL" || {
    echo "[ERROR] 依赖安装失败，请检查网络连接或 Python 环境"
    exit 1
  }
else
  "$PIP_CMD" install -r requirements.txt -i "$PIP_INDEX_URL" || {
    echo "[ERROR] 依赖安装失败，请检查网络连接或 Python 环境"
    exit 1
  }
fi

echo "[INFO] 依赖安装完成"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8888}"
FLASK_APP="${FLASK_APP:-app.py}"
FLASK_ENV="${FLASK_ENV:-production}"

URL="http://$HOST:$PORT"
echo "[INFO] 启动服务 $URL"
echo "[INFO] 服务启动后将自动打开浏览器..."

# 设置环境变量
export FLASK_APP="$FLASK_APP"
export FLASK_ENV="$FLASK_ENV"
export FLASK_HOST="$HOST"
export FLASK_PORT="$PORT"

# 检查 Flask 应用文件是否存在
if [ ! -f "$FLASK_APP" ]; then
    echo "[ERROR] 未找到应用文件: $FLASK_APP"
    exit 1
fi

# 确保使用虚拟环境中的 Python
PYTHON_CMD="$VENV/bin/python"
if [ ! -x "$PYTHON_CMD" ]; then
    echo "[ERROR] 虚拟环境中未找到 Python，请检查虚拟环境是否创建成功"
    exit 1
fi

# 后台启动服务，等待几秒后打开浏览器
echo "[INFO] 正在启动 Flask 服务..."
"$PYTHON_CMD" "$FLASK_APP" &
SERVER_PID=$!

# 等待服务启动
echo "[INFO] 等待服务启动..."
sleep 4

# 检查服务是否成功启动
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "[ERROR] 服务启动失败，请检查错误信息"
    exit 1
fi

# 自动打开浏览器
echo "[INFO] 正在打开浏览器..."
if command -v open >/dev/null 2>&1; then
    open "$URL" || echo "[WARN] 无法自动打开浏览器，请手动访问: $URL"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL" || echo "[WARN] 无法自动打开浏览器，请手动访问: $URL"
else
    echo "[INFO] 请手动在浏览器中访问: $URL"
fi

echo "[INFO] 服务已启动，按 Ctrl+C 停止服务"
echo "[INFO] 访问地址: $URL"

# 等待服务进程
wait $SERVER_PID

