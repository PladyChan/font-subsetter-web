#!/bin/bash

echo "开始安装和构建..."

# 安装 Homebrew（如果没有）
if ! command -v brew &> /dev/null; then
    echo "安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装 Anaconda（如果没有）
if ! command -v conda &> /dev/null; then
    echo "安装 Anaconda..."
    brew install --cask anaconda
    echo 'export PATH="/usr/local/anaconda3/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
fi

# 创建新的 conda 环境
echo "创建 Python 环境..."
conda create -n fonttools python=3.9 tk -y
conda activate fonttools

# 安装必要的包
echo "安装必要的包..."
pip install fonttools
pip install py2app

# 清理之前的构建
echo "清理之前的构建..."
rm -rf build dist

# 构建应用
echo "构建应用..."
python setup.py py2app

# 创建 DMG
echo "创建 DMG..."
hdiutil create -volname "字体精简工具" -srcfolder dist/字体精简工具.app -ov -format UDZO 字体精简工具.dmg

echo "完成！您可以在当前目录找到 字体精简工具.dmg" 