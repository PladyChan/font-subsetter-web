#!/bin/bash

echo "开始构建字体精简工具..."

# 检查并安装 Homebrew
if ! command -v brew &> /dev/null; then
    echo "正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装 python-tk
echo "正在安装 python-tk..."
brew install python-tk@3.9

# 安装必要的 Python 包
echo "正在安装必要的 Python 包..."
pip3 install fonttools
pip3 install py2app

# 清理之前的构建
echo "清理之前的构建..."
rm -rf build dist

# 构建应用
echo "开始构建应用..."
python3 setup.py py2app

# 创建 DMG
echo "创建 DMG 文件..."
hdiutil create -volname "字体精简工具" -srcfolder dist/字体精简工具.app -ov -format UDZO 字体精简工具.dmg

echo "构建完成！"
echo "您可以在当前目录找到 字体精简工具.dmg" 