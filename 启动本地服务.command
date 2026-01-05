#!/usr/bin/env bash
# TrimType字体裁剪工具 - 本地一键启动脚本
# Designed & Developed by Plady
#
# 使用说明：
#   1. 确保已安装 Python 3
#   2. 双击本文件即可启动本地服务
#   3. 启动成功后会自动打开浏览器访问

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 确保脚本有执行权限
chmod +x run_local.sh 2>/dev/null || true

# 执行启动脚本
echo "=========================================="
echo "  TrimType字体裁剪工具 - 本地服务启动器"
echo "  Designed & Developed by Plady"
echo "=========================================="
echo ""

./run_local.sh
EXIT_CODE=$?

# 如果脚本执行失败，保持窗口打开以便查看错误
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "  启动失败，请检查上面的错误信息"
    echo "=========================================="
    echo ""
    echo "按任意键退出..."
    read -n 1
fi

