#!/bin/bash

# 确保脚本在错误时停止
set -e

# 更新系统包
apt-get update
apt-get upgrade -y

# 安装必要的系统包
apt-get install -y python3-venv python3-pip nginx supervisor

# 创建项目目录
APP_DIR=/var/www/typetrim
mkdir -p $APP_DIR

# 复制应用文件
cp -r ../* $APP_DIR/

# 创建虚拟环境并安装依赖
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置 Supervisor
cp aliyun-deploy/supervisor.conf /etc/supervisor/conf.d/typetrim.conf
sed -i "s|/path/to/venv|$APP_DIR/venv|g" /etc/supervisor/conf.d/typetrim.conf
sed -i "s|/path/to/your/app|$APP_DIR|g" /etc/supervisor/conf.d/typetrim.conf

# 配置 Nginx
cp aliyun-deploy/nginx.conf /etc/nginx/sites-available/typetrim
sed -i "s|/path/to/your/app|$APP_DIR|g" /etc/nginx/sites-available/typetrim
ln -sf /etc/nginx/sites-available/typetrim /etc/nginx/sites-enabled/

# 重启服务
systemctl restart supervisor
systemctl restart nginx

echo "部署完成！请确保："
echo "1. 更新 nginx.conf 中的域名配置"
echo "2. 配置 SSL 证书"
echo "3. 设置正确的文件权限"