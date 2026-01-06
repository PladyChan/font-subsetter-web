#!/bin/bash
# 构建脚本 - 用于阿里内部部署平台

set -e

echo "========================================="
echo "开始构建 TrimType 应用..."
echo "========================================="

# 检查 Python 版本
python3 --version

# 升级 pip
echo "升级 pip..."
python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
echo "安装项目依赖..."
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "========================================="
echo "构建完成！"
echo "========================================="

