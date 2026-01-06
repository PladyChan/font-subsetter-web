#!/bin/bash
# 部署脚本 - 用于阿里内部部署平台启动服务

set -e

echo "========================================="
echo "启动 TrimType 应用..."
echo "========================================="

# 使用 gunicorn 启动 Flask 应用（生产环境推荐）
# 如果平台不支持 gunicorn，可以改用 Flask 内置服务器

# 检查 gunicorn 是否安装
if command -v gunicorn &> /dev/null; then
    echo "使用 Gunicorn 启动服务..."
    # Gunicorn 配置
    # -w: worker 进程数（根据 CPU 核心数调整）
    # -b: 绑定地址和端口
    # --timeout: 超时时间（字体处理可能需要较长时间）
    # --access-logfile: 访问日志
    # --error-logfile: 错误日志
    exec gunicorn -w 2 -b 0.0.0.0:${PORT:-8080} \
        --timeout 300 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        wsgi:app
else
    echo "使用 Flask 内置服务器启动..."
    # 如果 gunicorn 不可用，使用 Flask 内置服务器
    export FLASK_APP=wsgi.py
    export FLASK_ENV=production
    python3 -m flask run --host=0.0.0.0 --port=${PORT:-8080}
fi

